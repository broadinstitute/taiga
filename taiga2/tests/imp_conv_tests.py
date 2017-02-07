import pytest
import os

from flask_sqlalchemy import SessionBase

from taiga2.aws import aws
from taiga2.models import User, Folder, Dataset, Entry, DatasetVersion, DataFile, InitialFileType
from taiga2.controllers import models_controller
from taiga2.tasks import background_process_new_upload_session_file

test_files_folder_path = 'taiga2/tests/test_files'

raw_file_name = 'hello.txt'
raw_file_path = os.path.join(test_files_folder_path, raw_file_name)

csv_file_name = 'npcv1.csv'
csv_file_path = os.path.join(test_files_folder_path, csv_file_name)

@pytest.mark.parametrize("filename, initial_file_type", [
    (raw_file_name, InitialFileType.Raw.value),
    (csv_file_name, InitialFileType.NumericMatrixCSV.value)
])
def test_upload_session_file(filename, initial_file_type, session: SessionBase, user_id):
    new_bucket = aws.s3.Bucket('bucket')
    new_bucket.create()

    converted_s3_key = models_controller.generate_convert_key()

    with open(raw_file_path, 'rb') as data:
        aws.s3.Bucket(new_bucket.name).put_object(Key=converted_s3_key, Body=data)
    s3_raw_uploaded_file = aws.s3.Object(new_bucket.name, converted_s3_key)

    bucket_name = "bucket"
    initial_s3_key = s3_raw_uploaded_file.key

    session = models_controller.add_new_upload_session(user_id)
    upload_session_file = models_controller.add_upload_session_file(session.id, filename, initial_file_type, initial_s3_key, bucket_name)

    background_process_new_upload_session_file.delay(upload_session_file.id, initial_s3_key, initial_file_type, bucket_name,
                                                   converted_s3_key).wait()

    # confirm the converted object was published back to s3
    assert aws.s3.Object(bucket_name, converted_s3_key).download() is not None
