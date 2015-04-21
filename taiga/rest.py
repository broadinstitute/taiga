from injector import inject, Injector
from flask import Flask, render_template, request, make_response, session, flash, redirect
from flask import Blueprint, abort
from flask import jsonify
import flask

from sqlmeta import MetaStore, Hdf5Store
from convert import ConvertService, CacheService

rest = Blueprint('rest', __name__, template_folder='templates')

class InvalidParameters(Exception):
  status_code = 400
  
  def __init__(self, message):
    self.message = message
  
  def to_dict(self):
    return dict(message = self.message)

@rest.route("/rest/v0/datasets")
@inject(meta_store=MetaStore)
def list_datasets(meta_store):
  # http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api#pagination
  # if using pagination add header:
  # Link: <https://api.github.com/user/repos?page=3&per_page=100>; rel="next", <https://api.github.com/user/repos?page=50&per_page=100>; rel="last"
  # X-Total-Count
  """ Returns a json result with properties name, description, latest_date, version_count"""
  if 'tag' in request.values:
    datasets = meta_store.get_by_tag(request.values["tag"], None)
  else:
    datasets = meta_store.list_names(None)
  return jsonify(datasets=[x._asdict() for x in datasets])

@rest.route("/rest/v0/namedDataset")
@inject(meta_store=MetaStore, import_service=ConvertService, hdf5_store=Hdf5Store, cache_service=CacheService)
def get_dataset_by_name(meta_store, import_service, hdf5_store, cache_service):
  fetch = request.values['fetch']
  name = request.values['name']
  version = None
  if 'version' in request.values:
    version = request.values['version']
  dataset_id = meta_store.get_dataset_id_by_name(name, version)
  if fetch == "content":
        # drop parameters that have nothing to do with formatting the dataset result
        # perhaps there's a better way to do this.  Only copy the attributes that matter?
        parameters = dict(request.values.items())
        if "name" in parameters:
          del parameters['name']
        if "fetch" in parameters:
          del parameters['fetch']
        if 'version' in parameters:
            del parameters['version']
        return _get_dataset(meta_store, import_service, hdf5_store, cache_service, dataset_id, parameters)
  elif fetch == "id":
    return dataset_id
  else:
    raise InvalidParameters("Invalid value for fetch: %s" % fetch)

@rest.route("/rest/v0/triples/find", methods=["POST"])
@inject(meta_store=MetaStore)
def find_triples(meta_store):
  json = request.get_json(force=True)
  result = meta_store.exec_stmt_query(json['query'])
  return flask.jsonify(results=result)

@rest.route("/rest/v0/metadata/<dataset_id>")
@inject(meta_store=MetaStore)
def get_metadata(meta_store, dataset_id):
  meta = meta_store.get_dataset_by_id(dataset_id)
  if meta == None:
    abort(404)
  
  return jsonify(name=meta.name, created_timestamp=meta.created_timestamp, description=meta.description, created_by=meta.created_by, version=meta.version, is_published=meta.is_published, data_type=meta.data_type)

def generate_dataset_filename(meta_store, dataset_id, extension):
  ds = meta_store.get_dataset_by_id(dataset_id)
  filename = "".join([ x if x.isalnum() else "_" for x in ds.name ])
  return "%s_v%s.%s" % (filename, ds.version, extension)

# called by get_dataset.  The key difference here is that no parameters are directly pulled out of the request
def _get_dataset(meta_store, import_service, hdf5_store, cache_service, dataset_id, parameters):
  """ Write dataset in the response.  Options:
    format=tabular_csv|tabular_tsv|csv|tsv|hdf5

    matrix_csv and matrix_tsv:
       will fail if dims != 2
  """
  format = parameters['format']

  file_handle = cache_service.create_file_for(dict(dataset_id = dataset_id, parameters = parameters))

  metadata = meta_store.get_dataset_by_id(dataset_id)
  hdf5_path = metadata.hdf5_path
  if hdf5_path != None:
    if format == "tabular_csv":
      import_fn = lambda: import_service.hdf5_to_tabular_csv(hdf5_path, file_handle.name, delimiter=",")
      suffix = "csv"
    elif format == "tabular_tsv":
      import_fn = lambda: import_service.hdf5_to_tabular_csv(hdf5_path, file_handle.name, delimiter="\t")
      suffix = "tsv"
    elif format == "gct":
      import_fn = lambda: import_service.hdf5_to_gct(hdf5_path, file_handle.name)
      suffix = "gct"
    elif format == "tsv":
      import_fn = lambda: import_service.hdf5_to_csv(hdf5_path, file_handle.name, delimiter="\t")
      suffix = "tsv"
    elif format == "csv":
      import_fn = lambda: import_service.hdf5_to_csv(hdf5_path, file_handle.name, delimiter=",")
      suffix = "csv"
    elif format == "rdata":
      import_fn = lambda: import_service.hdf5_to_Rdata(hdf5_path, file_handle.name)
      suffix = "Rdata"
    elif format == "hdf5":
      return flask.send_file(os.path.abspath(os.path.join(hdf5_store.hdf5_root, hdf5_path)), as_attachment=True, attachment_filename=generate_dataset_filename(meta_store, dataset_id, "hdf5"))
    else:
      raise InvalidParameters("unknown format for tabular data: %s" % format)
  else:
    columnar_path = metadata.columnar_path
    if format == "tsv":
      import_fn = lambda: import_service.columnar_to_tcsv(columnar_path, file_handle.name, delimiter="\t")
      suffix = "tsv"
    elif format == "csv":
      import_fn = lambda: import_service.columnar_to_tcsv(columnar_path, file_handle.name, delimiter=",")
      suffix = "csv"
    elif format == "rdata":
      import_fn = lambda: import_service.columnar_to_Rdata(columnar_path, file_handle.name)
      suffix = "Rdata"
    else:
      raise InvalidParameters("unknown format for columnar data: %s" % format)

  if file_handle.needs_content:
    import_fn()
    file_handle.done()

  return flask.send_file(file_handle.name, as_attachment=True, attachment_filename=generate_dataset_filename(meta_store, dataset_id, suffix))


@rest.route("/rest/v0/datasets/<dataset_id>")
@inject(meta_store=MetaStore, import_service=ConvertService, hdf5_store=Hdf5Store, cache_service=CacheService)
def get_dataset(meta_store, import_service, hdf5_store, cache_service, dataset_id):
    return _get_dataset(meta_store, import_service, hdf5_store, cache_service, dataset_id, request.values)