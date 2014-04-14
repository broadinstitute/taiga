import sqlmeta
import tempfile
import os
from nose import with_setup
from sqlmeta import Ref

temp_filename = None

def find_temp_file():
  global temp_filename
  
  fd = tempfile.NamedTemporaryFile(delete=False)
  temp_filename = fd.name
  fd.close()
  os.unlink(temp_filename)

def cleanup_temp_file():
  if os.path.exists(temp_filename):
    os.unlink(temp_filename)

@with_setup(find_temp_file, cleanup_temp_file)
def test_basic_usages():
  meta = sqlmeta.MetaStore(temp_filename)
  names = meta.list_names()

  assert len(names) == 0

  meta.register_dataset("name1", "dsid1", "description1", None, "path1")
  meta.close()

  meta = sqlmeta.MetaStore(temp_filename)
  names = meta.list_names()
  assert len(names) == 1

  ds = meta.get_dataset_by_id("dsid1")

  assert ds.name == "name1"
  assert ds.description == "description1"
  assert ds.dataset_id == "dsid1"

  meta.close()

@with_setup(find_temp_file, cleanup_temp_file)
def test_multiple_names():
  meta = sqlmeta.MetaStore(temp_filename)

  meta.register_dataset("name1", "dsid1", "description1", None, "path1")
  meta.register_dataset("name2", "dsid2", "description2", None, "path2")
  names = meta.list_names()
  assert len(names) == 2

  meta.close()

@with_setup(find_temp_file, cleanup_temp_file)
def test_multiple_versions():
  meta = sqlmeta.MetaStore(temp_filename)

  meta.register_dataset("name1", "dsid1", "description1", None, "path1")
  versions = meta.get_dataset_versions("name1")
  assert len(versions) == 1

  meta.register_dataset("name1", "dsid1v2", "description1v2", None, "path1v2", True)
  versions = meta.get_dataset_versions("name1")
  assert len(versions) == 2

  assert meta.get_dataset_id_by_name("name1") == "dsid1v2"
  assert meta.get_dataset_id_by_name("name1", version=1) == "dsid1"
  assert meta.get_dataset_id_by_name("name1", version=2) == "dsid1v2"

  meta.close()
  
@with_setup(find_temp_file, cleanup_temp_file)
def test_update_description():
  meta = sqlmeta.MetaStore(temp_filename)

  meta.register_dataset("name1", "dsid1", "description1", None, "path1")
  meta.update_description("dsid1", "description updated")
  ds = meta.get_dataset_by_id("dsid1")
  
  assert ds.description == "description updated"

  meta.close()

@with_setup(find_temp_file, cleanup_temp_file)
def test_insert_and_query():
  meta = sqlmeta.MetaStore(temp_filename)
  
  meta.insert_stmt(Ref("x"), Ref("y"), Ref("z"))
  meta.insert_stmt(Ref("a"), Ref("y"), Ref("z"))
  meta.insert_stmt(Ref("a"), Ref("b"), Ref("z"))
  
  assert meta.find_stmt(Ref("x"), None, None) == [(Ref("x"),Ref("y"),Ref("z"))]
  assert meta.find_stmt(Ref("x"), Ref("y"), None) == [(Ref("x"),Ref("y"),Ref("z"))]
  assert meta.find_stmt(Ref("x"), Ref("y"), Ref("z")) == [(Ref("x"),Ref("y"),Ref("z"))]
  
  meta.close()

@with_setup(find_temp_file, cleanup_temp_file)
def test_insert_dups():
  meta = sqlmeta.MetaStore(temp_filename)
  
  meta.insert_stmt(Ref("x"), Ref("y"), Ref("z"))
  meta.insert_stmt(Ref("a"), Ref("y"), Ref("z"))
  meta.insert_stmt(Ref("a"), Ref("b"), Ref("z"))
  
  assert meta.find_stmt(Ref("x"), None, None) == [(Ref("x"),Ref("y"),Ref("z"))]
  assert meta.find_stmt(Ref("x"), Ref("y"), None) == [(Ref("x"),Ref("y"),Ref("z"))]
  assert meta.find_stmt(Ref("x"), Ref("y"), Ref("z")) == [(Ref("x"),Ref("y"),Ref("z"))]
  
  meta.close()

@with_setup(find_temp_file, cleanup_temp_file)
def test_delete():
  meta = sqlmeta.MetaStore(temp_filename)
  
  meta.insert_stmt(Ref("x"), Ref("y"), Ref("z"))
  meta.insert_stmt(Ref("a"), Ref("y"), Ref("z"))
  meta.delete_stmt(Ref("x"), Ref("y"), Ref("z"))

  assert meta.find_stmt(None, None, Ref("z")) == [(Ref("a"),Ref("y"),Ref("z"))]

  meta.close()
