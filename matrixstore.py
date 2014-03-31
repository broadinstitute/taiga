from collections import namedtuple
import uuid
import itertools
import h5py
import numpy as np
import csv
import triples
from triples import Ref
from contextlib import contextmanager

Dimension = namedtuple("Dimension", ["name", "values"])
DataSet = namedtuple("DataSet", ["id", "dims", "properties"])

HAS_TYPE = Ref("type:hasType")
DATASET = Ref("type:DataSet")
DATASET_PATH = Ref("dataset:path")
ATTRIBUTE_PREFIX = "attr:"

def gen_index_mapping(axis_selections):
  dest_indices = [range(len(x)) for x in axis_selections]
  for dest_index in itertools.product(*dest_indices):
    src_index = tuple([axis_selections[i][x] for i, x in enumerate(dest_index)])
    yield (src_index, dest_index)

@contextmanager
def open_hdf5_ctx_mgr(hdf5_path):
  f = h5py.File(hdf5_path, "r")
  yield f
  f.close()

class Store:
  def __init__(self, path, hdf5_open=open_hdf5_ctx_mgr):
    self.root_dir = path
    self.ts = triples.TripleStore(path+"/metadata.sqlite3")
    self.hdf5_open = open_hdf5_ctx_mgr
  
  def close(self):
    self.ts.close()
  
  def record_dataset(self, key_value_pairs, hdf5_path):
    'returns dataset id for newly created'

    with self.hdf5_open(hdf5_path) as f:
      dsid = f['data'].attrs["id"]
    
    self.ts.insert(Ref(dsid), HAS_TYPE, DATASET)
    self.ts.insert(Ref(dsid), DATASET_PATH, hdf5_path)
    self.add_annot(dsid, key_value_pairs)
    return dsid

  def get_hdf5_path(self, dataset_id):
    hdf5_path = self.ts.find(Ref(dataset_id), DATASET_PATH, None)[0][2]
    return hdf5_path

  # could create hdf5 of slice.  Use hash-content addressing to reuse hdf5 record if
  # slice has already been computed?
  def dense_slice(self, dataset_id, axis_selections):
    hdf5_path = self.get_hdf5_path(dataset_id)
    
    with self.hdf5_open(hdf5_path) as f:
      data = f['data']
      # TODO: would rather populate it with NAs.  Use NaN for missing values?
      region = np.zeros([len(x) for x in axis_selections],'f')
      for src_index, dest_index in gen_index_mapping(axis_selections):
        region[dest_index] = data[src_index]
    
    return region
    
  def slice(self, dataset_id, axis_selections, target):
    hdf5_path = self.get_hdf5_path(dataset_id)
    
    with self.hdf5_open(hdf5_path) as f:
      data = f['data']
      for src_index, dest_index in _gen_index_mapping(axis_selections):
        target.update(src_index, data[src_index])
    
    return rows

  def add_annot(self, dsid, key_value_pairs):
    for k,v in key_value_pairs:
      self.ts.insert(Ref(dsid), Ref(ATTRIBUTE_PREFIX+k), v)
  
  def rm_annot(self, dsid, key_value_pairs):
    for k,v in key_value_pairs:
      self.ts.delete(Ref(dsid), Ref(ATTRIBUTE_PREFIX+k), v)

  def get_metadata(self, dataset_id):
    hdf5_path = self.get_hdf5_path(dataset_id)
    
    with self.hdf5_open(hdf5_path) as f:
      attrs = list(f['data'].attrs.items())
      shape = f['data'].shape

      dims=[]
      for i in range(len(shape)):
        dim_vector = f['dim_%d' % i]
        dims.append( Dimension( name = dim_vector.attrs["name"], values = tuple(dim_vector)))
    
    properties = set([(x[1], x[2]) for x in self.ts.find(Ref(dataset_id), None, None)])
    return DataSet(id=dataset_id, dims=dims, properties=properties)

  def find(self, patterns):
    'patterns is a list of (key, value) pairs.  Value may be None, meaning, match anything'
    dsids = None
    for attr, value in patterns:
      found_dsids = set([x[0].id for x in self.ts.find(None, attr, value)])
      if dsids == None:
        dsids = found_dsids
      else:
        dsids = dsids.intersect(found_dsids)
    return dsids


def convert_csv_to_hdf5(filename, col_axis, row_axis, dest_directory):
  # TODO: Reduce memory footprint of this conversion
  with open(filename) as fd:
    r = csv.reader(fd)
    col_header = r.next()
    row_header = []
    rows = []
    for row in r:
      row_header.append(row[0])
      rows.append(row[1:])
  data = np.zeros((len(rows), len(rows[0])),'f')
  for row_i, row in enumerate(rows):
    for col_i, value in enumerate(row):
      data[row_i, col_i] = value

  dsid = str(uuid.uuid4())
  filename = "%s/%s.hdf5" % (dest_directory, dsid)

  f = h5py.File(filename, "w")
  str_dt = h5py.special_dtype(vlen=bytes)

  f['data'] = data
  f['data'].attrs['id'] = dsid
  
  dim_0 = f.create_dataset("dim_0", (len(row_header),), dtype=str_dt)
  dim_0[:] = row_header
  dim_0.attrs['name'] = row_axis

  dim_1 = f.create_dataset("dim_1", (len(col_header),), dtype=str_dt)
  dim_1[:] = col_header
  dim_1.attrs['name'] = col_axis
  f.close()

  return filename

