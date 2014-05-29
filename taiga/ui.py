from flask import Flask, render_template, request, make_response, session, flash, redirect
from flask import Blueprint, abort
import flask

import urllib

from collections import namedtuple
import collections

from tempfile import NamedTemporaryFile
import sqlmeta
from sqlmeta import Ref
from sqlmeta import MetaStore, Hdf5Store
from convert import ConvertService
import convert
import json

from injector import inject
import functools
import os

from flask.ext.openid import OpenID

def view(template_name):
  full_template_name = template_name + ".tpl"
  def decorator(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
      template_param = func(*args, **kwargs)
      return render_template(full_template_name, **template_param)
    return wrapped
  return decorator


ui = Blueprint('ui', __name__, template_folder='templates')
oid = OpenID()

@ui.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    """Does the login via OpenID.  Has to call into `oid.try_login`
    to start the OpenID machinery.
    """
    # if we are already logged in, go back to were we came from
    if 'openid' in session:
      return redirect(oid.get_next_url())
        
    openid = "https://crowd.broadinstitute.org:8443/openidserver/op"
    return oid.try_login(openid, ask_for=['email', 'fullname'])

@inject(meta_store=MetaStore)
def create_or_login(resp, meta_store):
    """This is called when login with OpenID succeeded and it's not
    necessary to figure out if this is the users's first login or not.
    This function has to redirect otherwise the user will be presented
    with a terrible URL which we certainly don't want.
    """
    session['openid'] = resp.identity_url
    # call this to force user record to get created
    meta_store.persist_user_details(resp.identity_url, email=resp.email, name=resp.fullname)
    flash(u'Successfully signed in')
    return redirect(oid.get_next_url())

@ui.route("/")
@view("index")
@inject(meta_store=MetaStore)
def index(meta_store):
  return {}

@ui.route("/datasets-by-timestamp")
@view("datasets-by-timestamp")
@inject(meta_store=MetaStore)
def datasets_by_timestamp(meta_store):
  datasets = meta_store.list_names()
  datasets.sort(lambda a, b: -cmp(a.created_timestamp, b.created_timestamp))

  return {'datasets': datasets}

@ui.route("/datasets-by-tag")
@view("datasets-by-tag")
@inject(meta_store=MetaStore)
def datasets_by_tag(meta_store):
  tags_and_counts = meta_store.get_all_tags()
  
  return {'tags': [dict(name=k, count=v) for k,v in tags_and_counts]}

@ui.route("/dataset/tagged")
@view("dataset/tagged")
@inject(meta_store=MetaStore)
def dataset_tagged(meta_store):
  tag = request.values["tag"]
  datasets = meta_store.get_by_tag(tag)
  return {'tag': tag, 'datasets': datasets}

@ui.route("/dataset/show/<dataset_id>")
@view("dataset/show")
@inject(meta_store=MetaStore, hdf5_store=Hdf5Store)
def dataset_show(meta_store, hdf5_store, dataset_id):
  meta = meta_store.get_dataset_by_id(dataset_id)
  if meta == None:
    abort(404)
    
  versions = meta_store.get_dataset_versions(meta.name)
  all_tags = [tag for tag, count in meta_store.get_all_tags()]
  dataset_tags = meta_store.get_dataset_tags(dataset_id)
  root_url = flask.current_app.config["ROOT_URL"]
  if meta.hdf5_path != None:
    formats = ['hdf5','gct','rdata','tabular_csv','tabular_tsv']
    dims = hdf5_store.get_dimensions(meta.hdf5_path)
  else:
    formats = ['csv','tsv','rdata']
    dims = []
  existing_data_types = json.dumps(meta_store.find_all_data_types())
  
  return {"root_url": root_url, "meta": meta, "dims":dims, "versions": versions, 
    "all_tags_as_json": json.dumps(list(all_tags)), "dataset_tags": dataset_tags,
    "existing_data_types": existing_data_types,
    "formats": formats}

@ui.route("/dataset/update", methods=["POST"])
@inject(meta_store=MetaStore)
def dataset_update(meta_store):
  j = request.form
  name = j['name']
  id = j['pk']
  if name == "tags":
    values = j.getlist("value[]")
    meta_store.update_tags(id, values)
  else:
    value = j['value']
    if name == "is_published":
      value = (value == "True")
      meta_store.update_dataset_field(id, name, value)
    elif name in ("description", "data_type", "is_published"):
      meta_store.update_dataset_field(id, name, value)
    else:
      raise Exception("Invalid field: %s" % name)

  # if this was invoked by a browser that wants to display something meaningful to the user
  if 'Accept' in request.headers:
    accept_types = request.headers['Accept'].split(",")
    if "text/html" in accept_types:
      return redirect("/dataset/show/%s" % id)
    
  return ""

def redirect_with_success(msg, url):
  flask.flash(msg, 'success')
  return flask.redirect(url)

def redirect_with_error(url, msg):
  flask.flash(msg, 'danger')
  return flask.redirect(url)

def _render_upload_form(meta_store, template):
  # make sure we're logged in before showing this form
  if not ('openid' in session):
    return redirect("/login?"+urllib.urlencode( (("next","/upload/tabular-form"),) ))
  
  existing_data_types = json.dumps(meta_store.find_all_data_types())
  
  params = {"existing_data_types": existing_data_types}
  if 'dataset_id' in request.values:
    existing_dsid = request.values['dataset_id']
    ds = meta_store.get_dataset_by_id(existing_dsid)
    params["new_version"] = "true"
    params["name"] = ds.name
    params["description"] = ds.description
  
  return render_template(template, **params)

@ui.route("/upload/columnar", methods=["POST"])
@inject(meta_store=MetaStore, import_service=ConvertService)
def upload_columnar(import_service, meta_store):
  if not ('openid' in session):
    # permission denied if not logged in
    abort(403)

  forms = request.form

  uploaded_file = request.files['file']
  name = forms['name']
  description = forms['description']
  created_by_user_id = meta_store.get_user_details(session['openid'])[0]
  is_published = (forms['is_published'] == "True")
  is_new_version_of_existing = 'overwrite_existing' in forms and (forms['overwrite_existing'] == "true")

  # check that name doesn't exist and matches is_new_version flag
  versions_exist = len(meta_store.get_dataset_versions(name)) > 0
  if not is_new_version_of_existing and versions_exist:
    return redirect_with_error("/upload/columnar-form", "There already exists a dataset with the name \"%s\"" % name)

  with NamedTemporaryFile() as temp_fd:
    temp_file = temp_fd.name
    uploaded_file.save(temp_file)
    
    # convert file
    dataset_id, columnar_path = meta_store.create_new_dataset_id(".columnar")
    import_service.tcsv_to_columnar(temp_file, columnar_path, "\t")

    meta_store.register_columnar_dataset(name, dataset_id, is_published, 
      description, created_by_user_id, columnar_path, is_new_version_of_existing)
    
  return redirect_with_success("Successfully imported file", "/dataset/show/%s" % dataset_id)

@ui.route("/upload/columnar-form")
@inject(meta_store=MetaStore)
def upload_columnar_form(meta_store):
  return _render_upload_form(meta_store, "/upload/columnar-form.tpl")

@ui.route("/upload/tabular", methods=["POST"])
@inject(meta_store=MetaStore, import_service=ConvertService)
def upload_tabular(import_service, meta_store):
  if not ('openid' in session):
    # permission denied if not logged in
    abort(403)

  forms = request.form

  uploaded_file = request.files['file']
  columns = forms['columns']
  rows = forms['rows']
  name = forms['name']
  description = forms['description']
  created_by_user_id = meta_store.get_user_details(session['openid'])[0]
  is_published = (forms['is_published'] == "True")
  data_type = forms['data_type']
  format = forms['format']
  is_new_version_of_existing = 'overwrite_existing' in forms and (forms['overwrite_existing'] == "true")

  # check that name doesn't exist and matches is_new_version flag

  versions_exist = len(meta_store.get_dataset_versions(name)) > 0
  if not is_new_version_of_existing and versions_exist:
    return redirect_with_error("/upload/tabular-form", "There already exists a dataset with the name \"%s\"" % name)

  with NamedTemporaryFile() as temp_fd:
    temp_file = temp_fd.name
    uploaded_file.save(temp_file)
    
    # convert file
    dataset_id, hdf5_path = meta_store.create_new_dataset_id(".hdf5")
    if format == "gct":
      import_service.gct_to_hdf5(temp_file, dataset_id, hdf5_path, columns, rows)
    else:
      if format == "csv":
        delimiter = ","
      elif format == "tsv":
        delimiter = "\t"
      else:
        raise Exception("Invalid format: %s" % format)
      import_service.tcsv_to_hdf5(temp_file, dataset_id, hdf5_path, columns, rows, delimiter)

    meta_store.register_dataset(name, dataset_id, is_published, 
      data_type,
      description, created_by_user_id, hdf5_path, is_new_version_of_existing)
    
  return redirect_with_success("Successfully imported file", "/dataset/show/%s" % dataset_id)

@ui.route("/upload/tabular-form")
@inject(meta_store=MetaStore)
def upload_tabular_form(meta_store):
  return _render_upload_form(meta_store, "/upload/tabular-form.tpl")
