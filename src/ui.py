from flask import Flask, render_template, request, make_response
from flask import Blueprint, abort
from flask import Config
import flask

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
@view("upload/tabular-form")
@inject(meta_store=MetaStore)
def upload_tabular_form(meta_store):
  params = {}
  if 'dataset_id' in request.values:
    existing_dsid = request.values['dataset_id']
    ds = meta_store.get_dataset_by_id(existing_dsid)
    params["new_version"] = "true"
    params["name"] = ds.name
    params["description"] = ds.description
  
  return params

def redirect_with_success(msg, url):
  return flask.redirect(url)

@ui.route("/upload/tabular", methods=["POST"])
@inject(meta_store=MetaStore, import_service=ConvertService)
def upload(import_service, meta_store):
  forms = request.form

  uploaded_file = request.files['file']
  columns = forms['columns']
  rows = forms['rows']
  name = forms['name']
  description = forms['description']
  created_by_user_id = None
  is_new_version = (forms['overwrite_existing'] == "true")

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
@inject(meta_store=MetaStore, import_service=ConvertService)
def get_dataset_by_name(meta_store, import_service):
  print "get_dataset_by_name, %s" % request.values
  fetch = request.values['fetch']
  print "get_dataset_by_name1"
  name = request.values['name']
  print "get_dataset_by_name2"
  version = None
  if 'version' in request.values:
    version = request.values['version']
  print "get_dataset_by_name3"
  dataset_id = meta_store.get_dataset_id_by_name(name, version)
  print "Fetch = %s" % fetch
  if fetch == "content":
    return get_dataset(meta_store, import_service, dataset_id)
  elif fetch == "id":
    return dataset_id
  else:
      abort(400, "Invalid value for fetch: %s" % fetch)

@rest.route("/rest/v0/datasets/<dataset_id>")
@inject(meta_store=MetaStore, import_service=ConvertService)
def get_dataset(meta_store, import_service, dataset_id):
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
    return flask.send_file(hdf5_path, as_attachment=True, attachment_filename="%s.hdf5" % dataset_id)
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
  
  injector = Injector(configure_injector)
  flask_injector.init_app(app=app, injector=injector)
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

