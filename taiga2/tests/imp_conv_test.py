import pytest
import os

import csv
from taiga2.tests.exp_conv_test import ProgressStub

from flask_sqlalchemy import SessionBase

from taiga2.aws import aws
from taiga2.models import (
    User,
    Folder,
    Dataset,
    Entry,
    DatasetVersion,
    DataFile,
    InitialFileType,
)
from taiga2.controllers import models_controller
from taiga2.tasks import background_process_new_upload_session_file
from taiga2.conv.imp import _get_csv_dims
from taiga2.conv import (
    csv_to_columnar,
    columnar_to_csv,
    columnar_to_rds,
    csv_to_hdf5,
    hdf5_to_csv,
)
from taiga2.conv.sniff import sniff2

test_files_folder_path = "taiga2/tests/test_files"

raw_file_name = "hello.txt"
raw_file_path = os.path.join(test_files_folder_path, raw_file_name)

csv_file_name = "tiny_matrix.csv"
csv_file_path = os.path.join(test_files_folder_path, csv_file_name)

tiny_table_name = "tiny_table.csv"
tiny_table_path = os.path.join(test_files_folder_path, tiny_table_name)

nonutf8_file_name = "non-utf8-table.csv"
nonutf8_file_path = os.path.join(test_files_folder_path, nonutf8_file_name)

# Not included in the git repository for space reasons. Add your own large numerical matrix in `test_files_folder_path`
# And uncomment where this file is used in tests
large_numerical_matrix_name = "large_numerical_matrix.csv"
large_numerical_matrix_path = os.path.join(
    test_files_folder_path, large_numerical_matrix_name
)

large_table_name = "large_table.csv"
large_table_path = os.path.join(test_files_folder_path, large_table_name)


@pytest.mark.parametrize(
    "filename, initial_file_type",
    [
        (raw_file_path, InitialFileType.Raw.value),
        (csv_file_path, InitialFileType.NumericMatrixCSV.value),
        (tiny_table_path, InitialFileType.TableCSV.value),
        # (large_numerical_matrix_path, InitialFileType.NumericMatrixCSV.value),
        # (large_table_path, InitialFileType.TableCSV.value)
    ],
)
def test_upload_session_file(
    filename, initial_file_type, session: SessionBase, user_id
):
    print("initial_file_type", initial_file_type, filename)

    new_bucket = aws.s3.Bucket("bucket")
    new_bucket.create()

    converted_s3_key = models_controller.generate_convert_key()
    compressed_s3_key = models_controller.generate_compressed_key()

    with open(filename, "rb") as data:
        aws.s3.Bucket(new_bucket.name).put_object(Key=converted_s3_key, Body=data)
    s3_raw_uploaded_file = aws.s3.Object(new_bucket.name, converted_s3_key)

    bucket_name = "bucket"
    initial_s3_key = s3_raw_uploaded_file.key

    session = models_controller.add_new_upload_session()
    upload_session_file = models_controller.add_upload_session_s3_file(
        session.id,
        os.path.basename(filename),
        initial_file_type,
        initial_s3_key,
        bucket_name,
        "UTF-8",
    )

    background_process_new_upload_session_file.delay(
        upload_session_file.id,
        initial_s3_key,
        initial_file_type,
        bucket_name,
        converted_s3_key,
        compressed_s3_key,
        upload_session_file.encoding,
    ).wait()

    # confirm the converted object was published back to s3
    assert aws.s3.Object(bucket_name, converted_s3_key).download_as_bytes() is not None

    # Check updated UploadSessionFile
    updated_upload_session_file = models_controller.get_upload_session_file(
        upload_session_file.id
    )
    if initial_file_type == InitialFileType.TableCSV.value:
        assert updated_upload_session_file.column_types_as_json is not None
    else:
        assert updated_upload_session_file.column_types_as_json is None


def test_get_csv_dims(tmpdir):
    filename = tmpdir.join("sample")
    filename.write_binary(b"a,b,c\nd,1,2,3\n")
    row_count, col_count, sha256, md5 = _get_csv_dims(
        ProgressStub(), str(filename), csv.excel, "utf-8"
    )
    assert row_count == 1
    assert col_count == 3
    assert sha256 == "629910bba467f4d6f518d309b3d2a99e316d7d5ef1faa744a7c5a6a084219255"
    assert md5 == "28ed28fa14570cc1409563f848a4c962"


def test_get_large_csv_dims_wrong_delimeter(tmpdir):
    filename = tmpdir.join("sample")
    file_contents = ",".join(str(i) for i in range(10000000))
    file_contents = "\n".join(file_contents for _ in range(3))
    file_contents = file_contents.encode("ascii")
    filename.write_binary(file_contents)

    with pytest.raises(Exception, match=r".*field larger than field limit.*"):
        row_count, col_count, sha256, md5 = _get_csv_dims(
            ProgressStub(), str(filename), csv.excel_tab, "utf-8"
        )


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


def test_matrix_with_full_header_import(tmpdir):
    r_filename = tmpdir.join("r_style")
    r_dest = tmpdir.join("r.hdf5")
    r_final = tmpdir.join("r_final.csv")
    r_filename.write_binary(b"a,b,c\nd,1,2,3\n")
    csv_to_hdf5(ProgressStub(), str(r_filename), str(r_dest))
    hdf5_to_csv(ProgressStub(), str(r_dest), lambda: str(r_final))

    pandas_filename = tmpdir.join("pandas_style")
    pandas_final = tmpdir.join("pandas_final.csv")
    pandas_dest = tmpdir.join("pandas.hdf5")
    pandas_filename.write_binary(b"i,a,b,c\nd,1,2,3\n")
    csv_to_hdf5(ProgressStub(), str(pandas_filename), str(pandas_dest))
    hdf5_to_csv(ProgressStub(), str(pandas_dest), lambda: str(pandas_final))

    assert r_final.read_binary() == pandas_final.read_binary()


def test_column_type_inference():
    tiny_table_column_types = sniff2(tiny_table_path, "UTF-8")
    assert tiny_table_column_types == {
        "a": "float",
        "b": "float",
        "c": "str",
        "d": "float",
    }

    nonutf8_column_types = sniff2(nonutf8_file_path, "UTF-8")
    assert nonutf8_column_types == {"row": "float", "validutf8": "str", "value": "str"}

    with pytest.raises(UnicodeDecodeError):
        sniff2(nonutf8_file_path, "ASCII")
