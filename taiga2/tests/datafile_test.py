import time

MAX_TIME = 5

def create_dataset(num_of_files=1):
    unimp()

def test_dataset_upload(app):
    with app.test_client() as c:
        mock_s3 = setup_mock_s3(app)

        dataset_version_id = create_dataset()

        start = time.time()
        resulting_urls = None
        while time.time() < start + MAX_TIME:
            r = c.get("/datafile?q="+dataset_version_id+"&format=csv")

            for prop in ['dataset_id', 'dataset_version_id', 'name', 'status']:
                assert r[prop] is not None

            if 'urls' in prop:
                resulting_urls = prop['urls']

        assert resulting_urls is not None
        assert len(prop["urls"]) == 1
        data = mock_s3.get(prop["urls"][0])

        assert data == "a,b\n1,2\n"
