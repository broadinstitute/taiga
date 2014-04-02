from bottle import route, run, auth_basic, post, redirect, install, request, response, app, static_file
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
  versions = meta_store.get_dataset_versions(meta.name)
  dims = hdf5_store.get_dimensions(meta.hdf5_path)
  return {"meta": meta, "dims":dims, "versions": versions}

@route("/dataset/update")
def dataset_update():
  meta_store = app().meta_store
  j = request.json
  assert j['name'] == "description"
  meta_store.update_description(j['pk'], j['value'])
  return ""

@route("/upload/tabular-form")
@view("upload/tabular-form")
def upload_tabular_form():
  params = {}
  meta_store = app().meta_store
  if 'dataset_id' in request.forms:
    existing_dsid = request.forms['dataset_id']
    ds = meta_store.get_dataset_by_id(existing_dsid)
    params["new_version"] = "true"
    params["name"] = ds.name
    params["description"] = ds.description
  
  return params

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

@route("/rest/v0/namedDataset")
def get_dataset_by_name():
  fetch = request.query.fetch
  name = request.query.name
  version = request.query.version
  meta_store = app().meta_store
  dataset_id = meta_store.get_dataset_id_by_name(name, version)
  if fetch == "content":
    return get_dataset(dataset_id)
  elif fetch == "id":
    return dataset_id
  else:
      abort(400, "Invalid value for fetch: %s" % fetch)

# define a common interface which can be used to create a view on multiple sources
# should we make it numpy like?  I suppose so.  So, we'd support "shape" and indexing,
# but not "fancy" indexing, and add a generator for enumerating non-nan elements
class SourceMatrix:
  def __init__(self, keys, dimensions):
    pass
  def get_selection_dimensions(self):
    pass
  def enumerate_coordinates(self):
    pass

@route("/rest/v0/datasets/<dataset_id>")
def get_dataset(dataset_id):
  """ Write dataset in the response.  Options: 
    format=tabular_csv|tabular_tsv|csv|tsv|hdf5
    
    matrix_csv and matrix_tsv:
       will fail if dims != 2
  """
  temp_fd = NamedTemporaryFile(delete=False)
  temp_file = temp_fd.name
  
  format = request.query.format
  meta_store = app().meta_store
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

if __name__ == "__main__":
  app().meta_store = sqlmeta.MetaDb("build/v2.sqlite3")
  app().hdf5_store = sqlmeta.Hdf5Fs("build")
  app().import_service = sqlmeta.ConvertService(app().hdf5_store)
  run(host='0.0.0.0', port=8999, debug=True)

