from flask import Flask, render_template, request
from flask import Blueprint, abort

from collections import namedtuple
from tempfile import NamedTemporaryFile
import sqlmeta
from sqlmeta import MetaStore, Hdf5Store
from convert import ConvertService
import convert

import flask_injector
from injector import inject, Injector

def view(template_name):
  full_template_name = template_name + ".tpl"
  def decorator(func):
    def wrapped(*args, **kwargs):
      template_param = func(*args, **kwargs)
      return render_template(full_template_name, **template_param)
    wrapped.__name__ = func.__name__
    return wrapped
  return decorator

ui = Blueprint('ui', __name__, template_folder='templates')
rest = Blueprint('rest', __name__, template_folder='templates')

@ui.route("/")
#@view("index")
@inject(meta_store=MetaStore)
def index(meta_store):
  print "returning dict"
  x = {'datasets': meta_store.list_names()}
  return render_template("index.tpl", **x)
  

@ui.route("/dataset/show/<dataset_id>")
@view("dataset/show")
@inject(meta_store=MetaStore, hdf5_store=Hdf5Store)
def dataset_show(meta_store, hdf5_store, dataset_id):
  meta = meta_store.get_dataset_by_id(dataset_id)
  versions = meta_store.get_dataset_versions(meta.name)
  dims = hdf5_store.get_dimensions(meta.hdf5_path)
  return {"meta": meta, "dims":dims, "versions": versions}

@ui.route("/dataset/update", methods=["POST"])
@inject(meta_store=MetaStore)
def dataset_update(meta_store):
  j = request.form
  assert j['name'] == "description"
  meta_store.update_description(j['pk'], j['value'])
  return ""

@ui.route("/upload/tabular-form")
@view("upload/tabular-form")
@inject(meta_store=MetaStore)
def upload_tabular_form(meta_store):
  params = {}
  if 'dataset_id' in request.query:
    existing_dsid = request.query['dataset_id']
    ds = meta_store.get_dataset_by_id(existing_dsid)
    params["new_version"] = "true"
    params["name"] = ds.name
    params["description"] = ds.description
  
  return params

def redirect_with_success(msg, url):
  redirect(url)

@ui.route("/upload/tabular", methods=["POST"])
@inject(meta_store=MetaStore, import_service=ConvertService)
def upload(import_service, meta_store):
  forms = request.form

  uploaded_file = request.files.get('file')
  columns = forms.get('columns')
  rows = forms.get('rows')
  name = forms.get('name')
  description = forms.get('description')
  created_by_user_id = None
  is_new_version = (forms.get('overwrite_existing') == "true")

  # TODO: check that name doesn't exist and matches is_new_version flag
  # if error, redirect to "/upload/csv-form"

  with NamedTemporaryFile() as temp_fd:
    temp_file = temp_fd.name
    uploaded_file.save(temp_file, overwrite=True)
    
    # convert file
    dataset_id, hdf5_path = import_service.convert_2d_csv_to_hdf5(temp_file, columns, rows)
    meta_store.register_dataset(name, dataset_id, description, created_by_user_id, hdf5_path, is_new_version)
    
  redirect_with_success("Successfully imported file", "/dataset/show/%s" % dataset_id)

@rest.route("/rest/v0/datasets")
@inject(meta_store=MetaStore)
def list_datasets(meta_store):
  # http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api#pagination
  # if using pagination add header:
  # Link: <https://api.github.com/user/repos?page=3&per_page=100>; rel="next", <https://api.github.com/user/repos?page=50&per_page=100>; rel="last"
  # X-Total-Count
  """ Returns a json result with properties name, description, latest_date, version_count"""
  return {'datasets': meta_store.list_names()}

@rest.route("/rest/v0/namedDataset")
@inject(meta_store=MetaStore)
def get_dataset_by_name(meta_store):
  fetch = request.query.fetch
  name = request.query.name
  version = request.query.version
  dataset_id = meta_store.get_dataset_id_by_name(name, version)
  if fetch == "content":
    return get_dataset(dataset_id)
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
  
  format = request.query.format
  import_service = app().import_service
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
    return static_file(hdf5_path, root='.', download="%s.hdf5" % dataset_id)
  else:
    abort("unknown format: %s" % format)

  return static_file(temp_file, root='/', download="%s.%s" % (dataset_id, suffix))
#  write_file(temp_file)
#  os.unlink(temp_file)

# I suspect there's a better way
def configure_injector(binder):
  print "configuring injector"
  meta_store = MetaStore("build/v3.sqlite")
  hdf5_store = Hdf5Store("build")
  binder.bind(MetaStore, to=meta_store)
  binder.bind(Hdf5Store, to=hdf5_store)

def create_app(config_filename):
  app = Flask(__name__)
#  app.config.from_pyfile(config_filename)

  injector = Injector([configure_injector])
  flask_injector.init_app(app=app, injector=injector)
  app.register_blueprint(ui)
  app.register_blueprint(rest)
  flask_injector.post_init_app(app=app, injector=injector)
  
  return app

if __name__ == "__main__":
  app = create_app("")
  app.run(host='0.0.0.0', port=8999, debug=True)

