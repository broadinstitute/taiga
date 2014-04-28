from flask import Flask, render_template, request, make_response, session, flash, redirect
from flask import Blueprint, abort
from flask import Config
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

import flask_injector
from injector import inject, Injector
import functools
import logging
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

def json_response(func):
  @functools.wraps(func)
  def wrapped(*args, **kwargs):
    python_dict = func(*args, **kwargs)
    resp = make_response(json.dumps(python_dict))
    resp.headers['Content-Type'] = 'application/json'
    return resp
  return wrapped

ui = Blueprint('ui', __name__, template_folder='templates')
rest = Blueprint('rest', __name__, template_folder='templates')
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
  tags = collections.defaultdict(lambda: 0)
  for subj, pred, obj in meta_store.find_stmt(None, Ref("hasTag"), None):
    tags[obj] += 1
  
  return {'datasets': meta_store.list_names(), 'tags': [dict(name=k, count=v) for k,v in tags.items()]}

@ui.route("/dataset/show/<dataset_id>")
@view("dataset/show")
@inject(meta_store=MetaStore, hdf5_store=Hdf5Store)
def dataset_show(meta_store, hdf5_store, dataset_id):
  meta = meta_store.get_dataset_by_id(dataset_id)
  if meta == None:
    abort(404)
    
  versions = meta_store.get_dataset_versions(meta.name)
  dims = hdf5_store.get_dimensions(meta.hdf5_path)
  all_tags = meta_store.get_all_tags()
  dataset_tags = meta_store.get_dataset_tags(dataset_id)
  
  return {"meta": meta, "dims":dims, "versions": versions, "all_tags_as_json": json.dumps(list(all_tags)), "dataset_tags": dataset_tags}

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
    assert name == "description"
    meta_store.update_description(id, j['value'])
  return ""

@ui.route("/upload/tabular-form")
@inject(meta_store=MetaStore)
def upload_tabular_form(meta_store):
  # make sure we're logged in before showing this form
  if not ('openid' in session):
    return redirect("/login?"+urllib.urlencode( (("next","/upload/tabular-form"),) ))
    
  params = {}
  if 'dataset_id' in request.values:
    existing_dsid = request.values['dataset_id']
    ds = meta_store.get_dataset_by_id(existing_dsid)
    params["new_version"] = "true"
    params["name"] = ds.name
    params["description"] = ds.description
  
  return render_template("upload/tabular-form.tpl", **params)

def redirect_with_success(msg, url):
  return flask.redirect(url)

@ui.route("/upload/tabular", methods=["POST"])
@inject(meta_store=MetaStore, import_service=ConvertService)
def upload(import_service, meta_store):
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
  is_new_version = 'overwrite_existing' in forms and (forms['overwrite_existing'] == "true")

  # TODO: check that name doesn't exist and matches is_new_version flag
  # if error, redirect to "/upload/csv-form"

  with NamedTemporaryFile() as temp_fd:
    temp_file = temp_fd.name
    uploaded_file.save(temp_file)
    
    # convert file
    dataset_id, hdf5_path = import_service.convert_2d_csv_to_hdf5(temp_file, columns, rows)
    meta_store.register_dataset(name, dataset_id, description, created_by_user_id, hdf5_path, is_new_version)
    
  return redirect_with_success("Successfully imported file", "/dataset/show/%s" % dataset_id)

@rest.route("/rest/v0/datasets")
@json_response
@inject(meta_store=MetaStore)
def list_datasets(meta_store):
  # http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api#pagination
  # if using pagination add header:
  # Link: <https://api.github.com/user/repos?page=3&per_page=100>; rel="next", <https://api.github.com/user/repos?page=50&per_page=100>; rel="last"
  # X-Total-Count
  """ Returns a json result with properties name, description, latest_date, version_count"""
  return {'datasets': meta_store.list_names()}

@rest.route("/rest/v0/namedDataset")
@inject(meta_store=MetaStore, import_service=ConvertService, hdf5_store=Hdf5Store)
def get_dataset_by_name(meta_store, import_service, hdf5_store):
  fetch = request.values['fetch']
  name = request.values['name']
  version = None
  if 'version' in request.values:
    version = request.values['version']
  dataset_id = meta_store.get_dataset_id_by_name(name, version)
  if fetch == "content":
    return get_dataset(meta_store, import_service, hdf5_store, dataset_id)
  elif fetch == "id":
    return dataset_id
  else:
      abort(400, "Invalid value for fetch: %s" % fetch)

@rest.route("/rest/v0/triples/find", methods=["POST"])
@inject(meta_store=MetaStore)
def find_triples(meta_store):
  json = request.get_json(force=True)
  result = meta_store.exec_stmt_query(json['query'])
  return flask.jsonify(results=result)

@rest.route("/rest/v0/metadata/<dataset_id>")
@json_response
@inject(meta_store=MetaStore)
def get_metadata(meta_store, dataset_id):
  meta = meta_store.get_dataset_by_id(dataset_id)
  if meta == None:
    abort(404)
  
  return {'name': meta.name}

@rest.route("/rest/v0/datasets/<dataset_id>")
@inject(meta_store=MetaStore, import_service=ConvertService, hdf5_store=Hdf5Store)
def get_dataset(meta_store, import_service, hdf5_store, dataset_id):
  """ Write dataset in the response.  Options: 
    format=tabular_csv|tabular_tsv|csv|tsv|hdf5
    
    matrix_csv and matrix_tsv:
       will fail if dims != 2
  """
  temp_fd = NamedTemporaryFile(delete=False)
  temp_file = temp_fd.name
  
  format = request.values['format']
  # TODO: rework this so we can clean up temp files
  hdf5_path = meta_store.get_dataset_by_id(dataset_id).hdf5_path
  if format == "tabular_csv":
    import_service.hdf5_to_tabular_csv(hdf5_path, temp_file, delimiter=",")
    suffix = "csv"
  elif format == "tabular_tsv":
    import_service.hdf5_to_tabular_csv(hdf5_path, temp_file, delimiter="\t")
    suffix = "tsv"
  elif format == "tsv":
    import_service.hdf5_to_csv(hdf5_path, temp_file, delimiter="\t")
    suffix = "tsv"
  elif format == "csv":
    import_service.hdf5_to_csv(hdf5_path, temp_file, delimiter=",")
    suffix = "csv"
  elif format == "hdf5":
    print "os.path.join(hdf5_store.hdf5_root, hdf5_path)", os.path.join(hdf5_store.hdf5_root, hdf5_path)
    return flask.send_file(os.path.abspath(os.path.join(hdf5_store.hdf5_root, hdf5_path)), as_attachment=True, attachment_filename="%s.hdf5" % dataset_id)
  else:
    abort("unknown format: %s" % format)

  return flask.send_file(temp_file, as_attachment=True, attachment_filename="%s.%s" % (dataset_id, suffix))
#  write_file(temp_file)
#  os.unlink(temp_file)

# I suspect there's a better way

def create_test_app(base_dir):
  app = Flask(__name__)

  app.config['TESTING'] = True
  app.config['DATA_DIR'] = base_dir
  setup_app(app)

  return app

def setup_app(app):
  def configure_injector(binder):
    data_dir = app.config['DATA_DIR']
    meta_store = MetaStore(data_dir+"/metadata.sqlite3")
    hdf5_store = Hdf5Store(data_dir)
    binder.bind(MetaStore, to=meta_store)
    binder.bind(Hdf5Store, to=hdf5_store)

  if "LOG_DIR" in app.config:
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(app.config['LOG_DIR']+"/taiga.log")
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)
  
  injector = Injector(configure_injector)
  flask_injector.init_app(app=app, injector=injector)
  oid.init_app(app)
  oid.after_login_func = injector.get(create_or_login)
  app.register_blueprint(ui)
  app.register_blueprint(rest)
  flask_injector.post_init_app(app=app, injector=injector)

def create_app():
  log = logging.getLogger(__name__)
  app = Flask(__name__)
  app.config.from_object("default_config")
  config_override_path = os.path.expanduser("~/.taiga/taiga.cfg")
  if os.path.exists(config_override_path):
    log.info("Loading config from %s" % config_override_path)
    app.config.from_pyfile(config_override_path)
  else:
    log.info("No file named %s.  Skipping" % config_override_path)
  setup_app(app)
  
  return app

if __name__ == "__main__":
  app = create_app()
  app.run(host='0.0.0.0', port=8999)

