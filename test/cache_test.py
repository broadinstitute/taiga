import tempfile
import os
import shutil
from taiga.convert import CacheService

def test_workflow():
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
