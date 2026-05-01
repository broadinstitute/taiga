import time
import taiga2.models as models
import taiga2.controllers.models_controller as mc
import json
from taiga2.tests.mock_s3 import parse_presigned_url
from taiga2.controllers.models_controller import find_datafile
import pytest

MAX_TIME = 5


class StubProgress:
    def progress(self, message):
        print(message)


def create_matrix_dataset_version(tmpdir, mock_s3):
    from taiga2.conv import csv_to_hdf5

    tmpsrc = str(tmpdir.join("thing.csv"))
    tmpdst = str(tmpdir.join("thing.hdf5"))

    with open(tmpsrc, "wt") as fd:
        fd.write("a,b\nc,1,2\n")

    csv_to_hdf5(StubProgress(), tmpsrc, tmpdst)

    # put data into mock S3
    mock_s3.Object("bucket", "key").upload_file(tmpdst)

    # create datafile
    df = mc.add_s3_datafile(
        name="dfname",
        s3_bucket="bucket",
        s3_key="key",
        compressed_s3_key="compressed/key",
        type=models.S3DataFile.DataFileFormat.HDF5,
        encoding="UTF-8",
        short_summary="short",
        long_summary="long",
    )

    ds = mc.add_dataset(
        name="dataset name", description="dataset description", datafiles_ids=[df.id]
    )
    return str(ds.dataset_versions[0].id)


def create_table_dataset_version(tmpdir, mock_s3):
    from taiga2.conv import csv_to_columnar

    tmpsrc = str(tmpdir.join("thing.csv"))
    tmpdst = str(tmpdir.join("thing.columnar"))

    with open(tmpsrc, "wt") as fd:
        fd.write("a,b\n1,2\n")

    csv_to_columnar(StubProgress(), tmpsrc, tmpdst)

    # put data into mock S3
    mock_s3.Object("bucket", "key").upload_file(tmpdst)

    # create datafile
    df = mc.add_s3_datafile(
        name="dfname",
        s3_bucket="bucket",
        s3_key="key",
        compressed_s3_key="compressed/key",
        type=models.S3DataFile.DataFileFormat.Columnar,
        encoding="UTF-8",
        short_summary="short",
        long_summary="long",
    )

    ds = mc.add_dataset(
        name="dataset name", description="dataset description", datafiles_ids=[df.id]
    )
    return str(ds.dataset_versions[0].id)


def _as_tsv(rows):
    content = "".join(["\t".join(row) + "\r\n" for row in rows])
    return content.encode("utf8")


@pytest.mark.parametrize(
    "src_format, out_format, is_expected",
    [
        ("table", "csv", lambda x: x == b"a,b\r\n1,2\r\n"),
        ("table", "tsv", lambda x: x == b"a\tb\r\n1\t2\r\n"),
        ("matrix", "csv", lambda x: x == b",a,b\r\nc,1.0,2.0\r\n"),
        ("matrix", "tsv", lambda x: x == b"\ta\tb\r\nc\t1.0\t2.0\r\n"),
        (
            "matrix",
            "gct",
            lambda x: x
            == _as_tsv(
                [
                    ["#1.2"],
                    ["1", "2"],
                    ["Name", "Description", "a", "b"],
                    ["c", "c", "1.0", "2.0"],
                ]
            ),
        ),
    ],
)
def test_dataset_export(
    app, session, db, mock_s3, user_id, tmpdir, src_format, out_format, is_expected
):
    assert user_id is not None

    with app.test_client() as c:
        if src_format == "table":
            dataset_version_id = create_table_dataset_version(tmpdir, mock_s3)
        else:
            dataset_version_id = create_matrix_dataset_version(tmpdir, mock_s3)

        start = time.time()
        resulting_urls = None
        while time.time() < start + MAX_TIME:
            r = c.get(
                "/datafile?dataset_version_id="
                + dataset_version_id
                + "&name=dfname&format="
                + out_format
            )
            assert r.status_code == 200, r.data.decode("utf8")
            response = json.loads(r.data.decode("utf8"))

            for prop in ["dataset_id", "dataset_version_id", "datafile_name", "status"]:
                assert response[prop] is not None

            print("status:", response)

            if "urls" in response:
                resulting_urls = response["urls"]
                print("resulting_urls", repr(resulting_urls))
                break

            time.sleep(0.1)

        assert resulting_urls is not None
        assert len(resulting_urls) == 1
        bucket, key = parse_presigned_url(resulting_urls[0])
        data = mock_s3.Object(bucket, key).download_as_bytes()

        assert is_expected(data)


def create_simple_dataset():
    # create datafile
    df = mc.add_s3_datafile(
        name="df",
        s3_bucket="bucket",
        s3_key="converted/key",
        compressed_s3_key="compressed/key",
        type=models.S3DataFile.DataFileFormat.Raw,
        encoding="UTF-8",
        short_summary="short",
        long_summary="long",
    )

    ds = mc.add_dataset(
        name="dataset name", description="dataset description", datafiles_ids=[df.id]
    )
    return ds.permaname, ds.dataset_versions[0].id, "df"


def test_find_datafile(session, db, user_id):
    permaname, dataset_version_id, datafile_name = create_simple_dataset()

    # using only permaname
    assert find_datafile(permaname, None, None, None) is not None

    # using permaname and version
    assert find_datafile(permaname, 1, None, None) is not None

    # using dataset version id
    assert find_datafile(None, None, dataset_version_id, None) is not None

    # using dataset version id and dataset name
    assert find_datafile(None, None, dataset_version_id, datafile_name) is not None

    # now make sure bad parameters can't find a dataset by accident
    # using only permaname
    assert find_datafile("invalid", None, None, None) is None

    # using permaname and version
    assert find_datafile(permaname, 2, None, None) is None

    # using dataset version id
    assert find_datafile(None, None, "invalid", None) is None

    # using dataset version id and dataset name
    assert find_datafile(None, None, dataset_version_id, "invalid") is None


@pytest.mark.parametrize(
    "client_storage_format, expected_conversion_types",
    [
        ("raw_hdf5_matrix", ["hdf5"]),
        ("raw_parquet_table", ["parquet"]),
    ],
)
def test_raw_files_with_known_format_get_proper_conversion_type(
    session, db, user_id, client_storage_format, expected_conversion_types
):
    df = mc.add_s3_datafile(
        name="testfile",
        s3_bucket="bucket",
        s3_key="key",
        compressed_s3_key=None,
        type=models.S3DataFile.DataFileFormat.Raw,
        encoding="UTF-8",
        short_summary="short",
        long_summary="long",
    )
    df.custom_metadata = {"client_storage_format": client_storage_format}
    db.session.commit()

    assert models.get_allowed_conversion_type(df) == expected_conversion_types


# ---------------------------------------------------------------------------
# Datafile preview endpoint tests
# ---------------------------------------------------------------------------

SAMPLE_PREVIEW = {
    "num_rows": 200,
    "num_columns": 5,
    "top_left_preview": {
        "column_names": ["a", "b", "c", "d", "e"],
        "row_names": ["r1", "r2", "r3"],
        "data": [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15]],
    },
}


def _create_s3_datafile():
    """Create a minimal S3 datafile and its parent dataset, returning the datafile."""
    df = mc.add_s3_datafile(
        name="preview_test_file",
        s3_bucket="bucket",
        s3_key="key",
        compressed_s3_key=None,
        type=models.S3DataFile.DataFileFormat.Raw,
        encoding="UTF-8",
        short_summary="short",
        long_summary="long",
    )
    mc.add_dataset(
        name="preview dataset",
        description="desc",
        datafiles_ids=[df.id],
    )
    return df


def test_post_and_get_datafile_preview(app, session, db, user_id):
    """POST creates a preview (201), GET returns it with all fields intact."""
    df = _create_s3_datafile()

    with app.test_client() as c:
        r = c.post(
            f"/datafile-preview/{df.id}",
            data=json.dumps(SAMPLE_PREVIEW),
            content_type="application/json",
        )
        assert r.status_code == 201

        r = c.get(f"/datafile-preview/{df.id}")
        assert r.status_code == 200
        body = json.loads(r.data)
        assert body["num_rows"] == 200
        assert body["num_columns"] == 5
        assert body["top_left_preview"]["column_names"] == ["a", "b", "c", "d", "e"]
        assert len(body["top_left_preview"]["data"]) == 3


def test_post_preview_replaces_existing(app, session, db, user_id):
    """A second POST to the same datafile overwrites (200), not duplicates."""
    df = _create_s3_datafile()

    with app.test_client() as c:
        c.post(
            f"/datafile-preview/{df.id}",
            data=json.dumps(SAMPLE_PREVIEW),
            content_type="application/json",
        )

        updated = {"num_rows": 500, "num_columns": 10}
        r = c.post(
            f"/datafile-preview/{df.id}",
            data=json.dumps(updated),
            content_type="application/json",
        )
        assert r.status_code == 200

        r = c.get(f"/datafile-preview/{df.id}")
        body = json.loads(r.data)
        assert body["num_rows"] == 500
        assert body["num_columns"] == 10
        assert body["top_left_preview"] is None


def test_post_preview_rejects_virtual_datafile(app, session, db, user_id):
    """POST on a virtual file returns 400 — previews belong on canonical files only."""
    df = _create_s3_datafile()
    vdf = mc.add_virtual_datafile(name="alias", datafile_id=df.id)

    with app.test_client() as c:
        r = c.post(
            f"/datafile-preview/{vdf.id}",
            data=json.dumps(SAMPLE_PREVIEW),
            content_type="application/json",
        )
        assert r.status_code == 400


def test_get_preview_resolves_virtual_datafile(app, session, db, user_id):
    """GET on a virtual file transparently returns the underlying canonical file's preview."""
    df = _create_s3_datafile()
    vdf = mc.add_virtual_datafile(name="alias", datafile_id=df.id)

    with app.test_client() as c:
        c.post(
            f"/datafile-preview/{df.id}",
            data=json.dumps(SAMPLE_PREVIEW),
            content_type="application/json",
        )

        r = c.get(f"/datafile-preview/{vdf.id}")
        assert r.status_code == 200
        body = json.loads(r.data)
        assert body["num_rows"] == 200
        assert body["num_columns"] == 5
