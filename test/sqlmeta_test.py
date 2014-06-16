from taiga import sqlmeta
from taiga.sqlmeta import Ref

import tempfile
import os
from nose import with_setup

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
  names = meta.list_names(None)

  assert len(names) == 0

  meta.register_dataset("name1", "dsid1", True, "data", "description1", None, "path1", True)
  meta.close()

  meta = sqlmeta.MetaStore(temp_filename)
  names = meta.list_names(None)
  assert len(names) == 1

  ds = meta.get_dataset_by_id("dsid1")

  assert ds.name == "name1"
  assert ds.description == "description1"
  assert ds.dataset_id == "dsid1"

  meta.close()

@with_setup(find_temp_file, cleanup_temp_file)
def test_multiple_names():
  meta = sqlmeta.MetaStore(temp_filename)

  meta.register_dataset("name1", "dsid1", True, "data", "description1", None, "path1", True)
  meta.register_dataset("name2", "dsid2", True, "data", "description2", None, "path2", True)
  names = meta.list_names(None)
  assert len(names) == 2

  meta.close()

@with_setup(find_temp_file, cleanup_temp_file)
def test_multiple_versions():
  meta = sqlmeta.MetaStore(temp_filename)

  meta.register_dataset("name1", "dsid1", True, "data", "description1", None, "path1", True)
  versions = meta.get_dataset_versions("name1")
  assert len(versions) == 1

  meta.register_dataset("name1", "dsid1v2", True, "data", "description1v2", None, "path1v2", True, True)
  versions = meta.get_dataset_versions("name1")
  assert len(versions) == 2

  assert meta.get_dataset_id_by_name("name1") == "dsid1v2"
  assert meta.get_dataset_id_by_name("name1", version=1) == "dsid1"
  assert meta.get_dataset_id_by_name("name1", version=2) == "dsid1v2"

  meta.close()
  
@with_setup(find_temp_file, cleanup_temp_file)
def test_update_dataset():
  meta = sqlmeta.MetaStore(temp_filename)

  meta.register_dataset("name1", "dsid1", True, "data", "description1", None, "path1", True)
  meta.update_dataset_field("dsid1", "description", "description updated")
  ds = meta.get_dataset_by_id("dsid1")

  assert ds.is_published  
  assert ds.description == "description updated"

  meta.update_dataset_field("dsid1", "data_type", "data_type updated")
  ds = meta.get_dataset_by_id("dsid1")
  
  assert ds.data_type == "data_type updated"

  meta.update_dataset_field("dsid1", "is_published",False)
  ds = meta.get_dataset_by_id("dsid1")
  
  assert not ds.is_published
  
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
