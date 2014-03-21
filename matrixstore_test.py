import h5py
from matrixstore import *
import numpy as np

#def testLoad():
#  f = h5py.File("test_data.hdf5", "w")
#  f['data'] = np.ones((2, 2), 'f')
#  f.close()
  
#  kv_pairs = [("name", "mat"), ("owner", "salad")]
#  dims = [Dimension("cellline", ["a", "b"]), Dimension("sample", ["c","d"])]
#  dsid = load( kv_pairs, dims, "test_data.hdf5" )

 # result = slice(dsid, [[0],[0,1]])
#  assert result.shape == (1,2)

def test_gen_index_mapping():
  l = [x for x in gen_index_mapping([[1],[2]]) ]
  assert l == [((1,2),(0,0))]
  
  l = [x for x in gen_index_mapping([[1],[2,3]])]
  assert l == [((1,2),(0,0)),((1,3),(0,1))]

#  slice(dsid, [[0],[0,1]], "test_dest.hdf5")
#  f = h5py.File("test_dest.hdf5", "r")
#  assert f.shape == (1,2)
#  f.close()


def test_convert_csv_to_hdf5():
  filename = convert_csv_to_hdf5("test_data/sample.tsv", "start_alphabet", "end_alphabet", "build")
  f = h5py.File(filename, "r")
  print f['data'].shape
  assert f['data'].shape == (2,3)
  assert f['data'][0,0] == 1.0
  assert f['data'][0,1] == 2.0
  assert f['data'][1,0] == 4.0
  
  assert f['dim_0'].shape == (2,)
  assert f['dim_1'].shape == (3,)

def test_find():
  s = Storage("build", hdf5_open=mock())
  dsid = s.record_dataset([("name","data set 1")],"data.hdf5")
  assert s.find([("name","data set 1")]) == [dsid]
  s.close()

def test_get_metadata():
  s = Storage("build", hdf5_open=mock())
  dsid = s.record_dataset([("name","data set 1")],"data.hdf5")
  meta = s.get_metadata(dsid)
  
  assert meta.id == dsid
  assert meta.dims == [Dimension(name="Alphabet", values=("A","B"))]
  assert ("name", "data set 1") in meta.properties
  
  s.close()

def test_dense_slice():
  raise

def test_sparse_slice():
  raise

# things to build:
# json/rest API for each of the operations:
#   - import data
#   - data slice
#   - query for datasets by (key, values)
#   - get metadata
