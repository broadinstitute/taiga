import time
import taiga2.models as models
import taiga2.controllers.models_controller as mc
import json
from taiga2.tests.monkeys import parse_presigned_url

MAX_TIME = 5


def create_dataset_version(tmpdir, user_id, monkey_s3):
    from taiga2.conv import csv_to_columnar

    tmpsrc = str(tmpdir.join("thing.csv"))
    tmpdst = str(tmpdir.join("thing.columnar"))

    with open(tmpsrc, "wt") as fd:
        fd.write("a,b\n1,2\n")

    csv_to_columnar(tmpsrc, tmpdst)

    # put data into mock S3
    monkey_s3.Object("bucket", "key").upload_file(tmpdst)

    # create datafile
    # TODO: I can definitely remove them, but when we discussed about this I was 3/4 at the end of s3_bucket/s3_key in a datafile
    df = mc.add_datafile(name="dfname",
                         s3_bucket='bucket',
                         s3_key='key',
                         url="s3://bucket/key",
                         type=models.DataFile.DataFileType.Columnar)

    ds = mc.add_dataset(name="dataset name", creator_id=user_id, description="dataset description", datafiles_ids=[df.id])
    return str(ds.dataset_versions[0].id)


def test_dataset_export(app, db, monkey_s3, user_id, tmpdir):
    assert user_id is not None

    with app.test_client() as c:
        dataset_version_id = create_dataset_version(tmpdir, user_id, monkey_s3)

        start = time.time()
        resulting_urls = None
        while time.time() < start + MAX_TIME:
            r = c.get("/api/datafile?dataset_version_id="+dataset_version_id+"&name=dfname&format=csv")
            assert r.status_code == 200
            response = json.loads(r.data.decode("utf8"))

            for prop in ['dataset_id', 'dataset_version_id', 'datafile_name', 'status']:
                assert response[prop] is not None

            print("status:", response['status'])

            if 'urls' in response:
                resulting_urls = response['urls']
                print("resulting_urls", repr(resulting_urls))
                break

            time.sleep(0.1)

        assert resulting_urls is not None
        assert len(resulting_urls) == 1
        bucket, key = parse_presigned_url(resulting_urls[0])
        data = monkey_s3.Object(bucket, key).download_as_bytes()

        assert data == b"a,b\r\n1,2\r\n"
