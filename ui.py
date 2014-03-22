from bottle import route, run, auth_basic, post, redirect, install, request, response, app
from bottle import jinja2_view as view, jinja2_template as template
from collections import namedtuple
from tempfile import NamedTemporaryFile
import sqlmeta

@route("/")
@view("index")
def index():
  meta_store = app().meta_store
  return {'datasets': meta_store.list_names()}

#@route("/dataset/list")
#@view("dataset/list")
#def dataset_list():

@route("/dataset/show/<dataset_id>")
@view("dataset/show")
def dataset_show(dataset_id):
  meta_store = app().meta_store
  hdf5_store = app().hdf5_store
  meta = meta_store.get_dataset_by_id(dataset_id)
  dims = hdf5_store.get_dimensions(meta.hdf5_path)
  return {"meta": meta, "dims":dims}

@route("/upload/tabular-form")
@view("upload/tabular-form")
def upload_tabular_form():
  return {}

def redirect_with_success(msg, url):
  redirect(url)

@route("/upload/tabular", method="POST")
def upload():
  forms = request.forms

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
    dataset_id, hdf5_path = app().import_service.convert_2d_csv_to_hdf5(temp_file, columns, rows)
    app().meta_store.register_dataset(name, dataset_id, description, created_by_user_id, hdf5_path, is_new_version)
    
  redirect_with_success("Successfully imported file", "/dataset/show/%s" % dataset_id)

@route("/rest/v0/datasets")
def list_datasets():
  # http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api#pagination
  # if using pagination add header:
  # Link: <https://api.github.com/user/repos?page=3&per_page=100>; rel="next", <https://api.github.com/user/repos?page=50&per_page=100>; rel="last"
  # X-Total-Count
  """ Returns a json result with properties name, description, latest_date, version_count"""
  meta_store = app().meta_store
  return {'datasets': meta_store.list_names()}

@route("/rest/v0/datasets/<dataset_id>")
def get_dataset(dataset_id):
  """ Write dataset in the response.  Options: 
    format=matrix_csv|matrix_tsv|csv|tsv|hdf5
    
    matrix_csv and matrix_tsv:
       will fail if dims != 2
  """
  format = request.param.get("format")
  hdf5_path = meta_store.get_hdf5_path(dataset_id)
  if format == "matrix_csv":
    temp_file = export_service.convert_hdf5_to_csv(hdf5_path, delimiter=",")
  elif format == "matrix_tsv":
    temp_file = export_service.convert_hdf5_to_csv(hdf5_path, delimiter="\t")
  else:
    error("unknown format: %s" % format)

  write_file(temp_file)

  os.unlink(temp_file)

if __name__ == "__main__":
  app().meta_store = sqlmeta.MetaDb("build/v2.sqlite3")
  app().hdf5_store = sqlmeta.Hdf5Fs("build")
  app().import_service = sqlmeta.ImportService(app().hdf5_store)
  run(host='0.0.0.0', port=8999, debug=True)

