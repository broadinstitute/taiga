import ui
import tempfile
import os
import shutil
import sqlmeta
from IPython import embed
from StringIO import StringIO

# 2x2 matrix
sample_tabular_contents = "a,b\nx,0,1\ny,2,3\n"
sample_after_processing = 'a,b\r\nx,0.0,1.0\r\ny,2.0,3.0\r\n'

def test_workflow():
  tempdir = tempfile.mkdtemp("ui-test")
  
  app = ui.create_test_app(tempdir)
  c = app.test_client()

  resp = c.get("/")
  assert resp.status_code == 200

  # make sure the form page renders
  resp = c.get("/upload/tabular-form")
  assert resp.status_code == 200

  resp = c.post("/upload/tabular", data=dict(
    file=(StringIO(sample_tabular_contents), 'test.txt'),
    columns="cols",
    rows="rows",
    name="name",
    description="desc",
    overwrite_existing="false"
  ))
  assert resp.status_code == 302
  dataset_id = resp.location.split("/")[-1]

  resp = c.get("/dataset/show/"+dataset_id)
  assert resp.status_code == 200

  resp = c.post("/dataset/update", data=dict(
    name="description", 
    pk=dataset_id,
    value="new_desc"))
  assert resp.status_code == 200

  shutil.rmtree(tempdir)

def test_rest_endpoints():
  tempdir = tempfile.mkdtemp("ui-test")
  app = ui.create_test_app(tempdir)
  c = app.test_client()

  resp = c.post("/upload/tabular", data=dict(
    file=(StringIO(sample_tabular_contents), 'test.txt'),
    columns="cols",
    rows="rows",
    name="name",
    description="desc",
    overwrite_existing="false"
  ))
  assert resp.status_code == 302
  dataset_id = resp.location.split("/")[-1]

  resp = c.get("/rest/v0/datasets")
  assert resp.status_code == 200

  resp = c.get("/rest/v0/namedDataset", query_string=dict(fetch="content", name="name", format="tabular_csv"))
  assert resp.status_code == 200
  assert resp.data == sample_after_processing
  
  resp = c.get("/rest/v0/namedDataset", query_string=dict(fetch="id", name="name", format="tabular_csv"))
  assert resp.status_code == 200
  assert resp.data == dataset_id

  resp = c.get("/rest/v0/datasets/"+dataset_id, query_string=dict(format="tabular_csv"))
  assert resp.status_code == 200
  assert resp.data == sample_after_processing
