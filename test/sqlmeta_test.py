import sqlmeta
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
  meta = sqlmeta.MetaDb(temp_filename)
  names = meta.list_names()

  assert len(names) == 0

  meta.register_dataset("name1", "dsid1", "description1", None, "path1")
  meta.close()

  meta = sqlmeta.MetaDb(temp_filename)
  names = meta.list_names()
  assert len(names) == 1

  ds = meta.get_dataset_by_id("dsid1")

  assert ds.name == "name1"
  assert ds.description == "description1"
  assert ds.dataset_id == "dsid1"

  meta.close()

@with_setup(find_temp_file, cleanup_temp_file)
def test_multiple_names():
  meta = sqlmeta.MetaDb(temp_filename)

  meta.register_dataset("name1", "dsid1", "description1", None, "path1")
  meta.register_dataset("name2", "dsid2", "description2", None, "path2")
  names = meta.list_names()
  assert len(names) == 2

  meta.close()

@with_setup(find_temp_file, cleanup_temp_file)
def test_multiple_versions():
  meta = sqlmeta.MetaDb(temp_filename)

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
  meta = sqlmeta.MetaDb(temp_filename)

  meta.register_dataset("name1", "dsid1", "description1", None, "path1")
  meta.update_description("dsid1", "description updated")
  ds = meta.get_dataset_by_id("dsid1")
  
  assert ds.description == "description updated"

  meta.close()
