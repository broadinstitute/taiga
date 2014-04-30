from injector import inject, Injector
from flask import Flask, render_template, request, make_response, session, flash, redirect
from flask import Blueprint, abort
from flask import jsonify
import flask

from sqlmeta import MetaStore, Hdf5Store
from convert import ConvertService
from tempfile import NamedTemporaryFile

rest = Blueprint('rest', __name__, template_folder='templates')

@rest.route("/rest/v0/datasets")
@inject(meta_store=MetaStore)
def list_datasets(meta_store):
  # http://www.vinaysahni.com/best-practices-for-a-pragmatic-restful-api#pagination
  # if using pagination add header:
  # Link: <https://api.github.com/user/repos?page=3&per_page=100>; rel="next", <https://api.github.com/user/repos?page=50&per_page=100>; rel="last"
  # X-Total-Count
  """ Returns a json result with properties name, description, latest_date, version_count"""
  return jsonify(datasets=meta_store.list_names())

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
@inject(meta_store=MetaStore)
def get_metadata(meta_store, dataset_id):
  meta = meta_store.get_dataset_by_id(dataset_id)
  if meta == None:
    abort(404)
  
  return jsonify(name=meta.name)

def generate_dataset_filename(meta_store, dataset_id, extension):
  ds = meta_store.get_dataset_by_id(dataset_id)
  filename = "".join([ x if x.isalnum() else "_" for x in ds.name ])
  return "%s_v%s.%s" % (filename, ds.version, extension)

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
    return flask.send_file(os.path.abspath(os.path.join(hdf5_store.hdf5_root, hdf5_path)), as_attachment=True, attachment_filename=generate_dataset_filename(meta_store, dataset_id, "hdf5"))
  else:
    abort("unknown format: %s" % format)

  return flask.send_file(temp_file, as_attachment=True, attachment_filename=generate_dataset_filename(meta_store, dataset_id, suffix))
