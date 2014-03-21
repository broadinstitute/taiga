from bottle import route, run, auth_basic, post, redirect, install, request, response, app
from bottle import jinja2_view as view, jinja2_template as template
from collections import namedtuple
from tempfile import NamedTemporaryFile
import matrixstore

@route("/")
@view("index")
def index():
  ms = app().matrix_store

  dsids = ms.find( [(matrixstore.HAS_TYPE, matrixstore.DATASET)] )
  
  return { "datasets": [ms.get_metadata(dsid) for dsid in dsids] }

def find_property(meta, key):
  return "fake-"+key

@route("/dataset/show/<dataset_id>")
@view("dataset_show")
def dataset_show(dataset_id):
  ms = app().matrix_store
  meta = ms.get_metadata(dataset_id)
  name = find_property(meta, "name")
  return {"meta": meta, "name": name}

@route("/upload", method="POST")
def upload():
  print "uploaded_file = %s" % (repr(request.files))
  uploaded_file = request.files.get('file')
  columns = request.forms.get('columns')
  rows = request.forms.get('rows')
  name = request.forms.get('name')
  owner = request.forms.get('owner')
  description = request.forms.get('description')
  
  with NamedTemporaryFile() as temp_fd:
    temp_file = temp_fd.name
    uploaded_file.save(temp_file, overwrite=True)
    hdf5_file = matrixstore.convert_csv_to_hdf5(temp_file, columns, rows, "build")
    ms = app().matrix_store
    key_value_pairs = [ 
      ("name", name),
      ("owner", owner),
      ("description", description)
    ]
    return ms.record_dataset(key_value_pairs, hdf5_file)

# named_data(named_data_id, name, latest_version)
# data_version(data_id, named_data_id, version_id, description, created_date, created_by_user_id)
# owner = (user_id, name, email, api_token)

@route("/rest/v0/datasets")
def list_datasets():
  # http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api#pagination
  # if using pagination add header:
  # Link: <https://api.github.com/user/repos?page=3&per_page=100>; rel="next", <https://api.github.com/user/repos?page=50&per_page=100>; rel="last"
  # X-Total-Count
  """ Returns a json result with properties name, description, latest_date, version_count"""
  
@route("/rest/v0/datasets/<dataset_id>")
def get_dataset():
  """ Write dataset in the response.  Options: 
    format=matrix_csv|matrix_tsv|csv|tsv|hdf5
    
    matrix_csv and matrix_tsv:
       will fail if dims != 2
  """
  

if __name__ == "__main__":
  app().matrix_store = matrixstore.Store("build")
  run(host='0.0.0.0', port=8999, debug=True)

