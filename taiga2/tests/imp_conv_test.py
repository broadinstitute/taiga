import pytest
import os

import csv
from taiga2.tests.exp_conv_test import ProgressStub

from flask_sqlalchemy import SessionBase

from taiga2.aws import aws
from taiga2.models import User, Folder, Dataset, Entry, DatasetVersion, DataFile, InitialFileType
from taiga2.controllers import models_controller
from taiga2.tasks import background_process_new_upload_session_file
from taiga2.conv.imp import _get_csv_dims
from taiga2.conv import csv_to_columnar, columnar_to_csv, columnar_to_rds

test_files_folder_path = 'taiga2/tests/test_files'

raw_file_name = 'hello.txt'
raw_file_path = os.path.join(test_files_folder_path, raw_file_name)

csv_file_name = 'tiny_matrix.csv'
csv_file_path = os.path.join(test_files_folder_path, csv_file_name)

nonutf8_file_name = "non-utf8-table.csv"
nonutf8_file_path = os.path.join(test_files_folder_path, nonutf8_file_name)

@pytest.mark.parametrize("filename, initial_file_type", [
    (raw_file_path, InitialFileType.Raw.value),
    (csv_file_path, InitialFileType.NumericMatrixCSV.value)
])
def test_upload_session_file(filename, initial_file_type, session: SessionBase, user_id):
    print("initial_file_type", initial_file_type, filename)

    new_bucket = aws.s3.Bucket('bucket')
    new_bucket.create()

    converted_s3_key = models_controller.generate_convert_key()

    with open(filename, 'rb') as data:
        aws.s3.Bucket(new_bucket.name).put_object(Key=converted_s3_key, Body=data)
    s3_raw_uploaded_file = aws.s3.Object(new_bucket.name, converted_s3_key)

    bucket_name = "bucket"
    initial_s3_key = s3_raw_uploaded_file.key

    session = models_controller.add_new_upload_session()
    upload_session_file = models_controller.add_upload_session_file(session.id, os.path.basename(filename), initial_file_type, initial_s3_key, bucket_name)

    background_process_new_upload_session_file.delay(upload_session_file.id, initial_s3_key, initial_file_type, bucket_name,
                                                   converted_s3_key).wait()

    # confirm the converted object was published back to s3
    assert aws.s3.Object(bucket_name, converted_s3_key).download_as_bytes() is not None


def test_get_csv_dims(tmpdir):
    filename = tmpdir.join("sample")
    filename.write_binary(b"a,b,c\nd,1,2,3\n")
    row_count, col_count, sha256 = _get_csv_dims(ProgressStub(), str(filename), csv.excel, "utf-8")
    assert row_count == 1
    assert col_count == 3
    assert sha256 == "629910bba467f4d6f518d309b3d2a99e316d7d5ef1faa744a7c5a6a084219255"

def test_non_utf8(tmpdir):
    dest = str(tmpdir.join("dest.columnar"))
    final = str(tmpdir.join("final.csv"))
    rds_dest = str(tmpdir.join("final.rds"))

    csv_to_columnar(None, nonutf8_file_path, dest)
    columnar_to_csv(None, dest, lambda: final)
    import csv
    with open(final, "rU") as fd:
        r = csv.DictReader(fd)
        row1 = next(r)
        assert row1["row"] == "1"
        assert len(row1["value"]) == 1
        row2 = next(r)
        assert row2["row"] == "2"
        assert row2["value"] == "R"

    # lastly, make sure we don't get an exception when converting to rds because R has its own ideas about encoding
    columnar_to_rds(None, dest, lambda: rds_dest)