import tempfile
import os
import shutil
from taiga.convert import CacheService

def test_end_to_end():
  tempdir = tempfile.mkdtemp("cache-test")

  cache_service = CacheService(tempdir)
  file = cache_service.create_file_for(dict(a="x", b="y"))
  
  # new file, so it needs content
  assert file.needs_content
  
  # write some content and signal the file is done
  with open(file.name, "w") as fd:
    fd.write("body")
  file.done()
  
  # attempt to fetch again
  file2 = cache_service.create_file_for(dict(a="x", b="y"))

  assert not file2.needs_content
  with open(file.name) as fd:
    assert fd.read() == "body"

  # make sure different parameters give us a different file
  file3 = cache_service.create_file_for(dict(a="z"))

  shutil.rmtree(tempdir)

def test_failed_to_generate():
  tempdir = tempfile.mkdtemp("cache-test")

  cache_service = CacheService(tempdir)

  file = cache_service.create_file_for(dict(a="x", b="y"))
  
  # new file, so it needs content
  assert file.needs_content

  # open the file to create it
  temp_filename_1 = file.name
  with open(file.name, "w") as fd:
    pass
    
  # before file.done() gets called, fetch the same key
  file2 = cache_service.create_file_for(dict(a="x", b="y"))

  # the file was not finished, so we still need content
  assert file2.needs_content
  assert file2.name != temp_filename_1

  shutil.rmtree(tempdir)
