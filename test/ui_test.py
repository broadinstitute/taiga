import tempfile
import os
import shutil
#from IPython import embed
from StringIO import StringIO
import json

import taiga.app
from taiga import ui
from taiga import sqlmeta

# 2x2 matrix
sample_tabular_contents = "a,b\nx,0,1\ny,2,3\n"
sample_after_processing = 'a,b\r\nx,0.0,1.0\r\ny,2.0,3.0\r\n'

def create_fake_user(tempdir, openid):
  meta_store =sqlmeta.MetaStore(tempdir+"/metadata.sqlite3")
  meta_store.persist_user_details(openid, email='mock-email', name='mock-name')
  meta_store.close()

def test_workflow():
  tempdir = tempfile.mkdtemp("ui-test")
  
  app = taiga.app.create_test_app(tempdir)
  create_fake_user(tempdir, "mockopenid")

  with app.test_client() as c:
    with c.session_transaction() as sess:
      sess['openid'] = 'mockopenid'

    resp = c.get("/")
    assert resp.status_code == 200

    # make sure the form page renders
    resp = c.get("/upload/tabular-form")
    assert resp.status_code == 200

    resp = c.post("/upload/tabular", data=dict(
      file=(StringIO(sample_tabular_contents), 'test.txt'),
      columns="cols",
      rows="rows",
      name="test-dataset-name",
      description="desc",
      overwrite_existing="false",
      is_published = "false",
      data_type = "data"      
    ))
    assert resp.status_code == 302
    dataset_id = resp.location.split("/")[-1]

    resp = c.post("/dataset/update", data={"name":"tags", "value[]":"test-tag-name", "pk":dataset_id})
    assert resp.status_code == 200

    resp = c.get("/datasets-by-tag")
    assert resp.status_code == 200
    assert "test-tag-name" in resp.get_data()
    
    resp = c.get("/dataset/tagged?tag=test-tag-name")
    assert resp.status_code == 200
    assert "test-dataset-name" in resp.get_data()
    
    resp = c.get("/datasets-by-timestamp")
    assert resp.status_code == 200
    assert "test-dataset-name" in resp.get_data()

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
  app = taiga.app.create_test_app(tempdir)
  create_fake_user(tempdir, "mockopenid")

  with app.test_client() as c:
    with c.session_transaction() as sess:
      sess['openid'] = 'mockopenid'

    resp = c.post("/upload/tabular", data=dict(
      file=(StringIO(sample_tabular_contents), 'test.txt'),
      columns="cols",
      rows="rows",
      name="name",
      description="desc",
      overwrite_existing="false",
      is_published = "false",
      data_type = "data"      
    ))
    assert resp.status_code == 302
    dataset_id = resp.location.split("/")[-1]

    resp = c.post("/dataset/update", data={"name":"tags", "value[]":"tag1", "pk":dataset_id})
    assert resp.status_code == 200

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

    resp = c.post("/rest/v0/triples/find", data=json.dumps({"query":[[{"var":"dataset"}, {"id":"hasTag"}, {"var":"tag"}]]}))
    assert resp.status_code == 200
    json_resp = json.loads(resp.data)
    assert json_resp["results"] == [{"dataset": {"id":dataset_id}, "tag": "tag1"}]
  