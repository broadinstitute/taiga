import datetime
import pytest

from freezegun import freeze_time
from flask_sqlalchemy import SessionBase

import taiga2.controllers.models_controller as models_controller
import taiga2.controllers.endpoint as endpoint
from taiga2.tests.test_models import new_dummy_folder, new_user

from taiga2.tasks import background_process_new_datafile, print_config

from taiga2.models import User, Folder, Dataset, Entry, DatasetVersion, DataFile
from taiga2.models import generate_permaname

from taiga2.aws import aws

from taiga2.tests.monkeys import MonkeyBucket

from flask import g

import boto3
from moto import mock_s3

import json


@pytest.fixture
def new_session_upload():
    _new_sessionUpload = models_controller.add_new_upload_session()
    return _new_sessionUpload


# @pytest.fixture
# @mock_s3
# def new_s3_credentials():
#     json_frontend_credentials = endpoint.get_s3_credentials()
#     _new_s3_credentials = json.loads(json_frontend_credentials)
#
#     return _new_s3_credentials


# @pytest.fixture
# @mock_s3
# def s3():
#     _s3 = boto3.resource('s3')
#     return _s3


# @pytest.fixture
# def bucket(s3):
#     s3 = boto3.resource('s3')
#     bucket_name = 'test_bucket'
#     s3.Bucket(bucket_name).create()
#     _test_bucket = s3.Bucket(bucket_name)
#
#     return _test_bucket


@pytest.fixture
def new_raw_uploaded_file(session: SessionBase,
                          new_session_upload):
    filename = "hello.txt"
    enumed_filetype = DataFile.DataFileType.Raw
    location = 'unknown'

    # Upload the file
    file_key = filename
    # s3.Object(bucket.name, file_key).upload_file('test_files/' + file_key)

    # TODO: Url needs to be fixed somehow. Do we really need it then?
    _new_raw_uploadFile = models_controller.add_upload_session_file(new_session_upload.id,
                                                                    filename=filename,
                                                                    filetype=enumed_filetype,
                                                                    url=location)

    return _new_raw_uploadFile


@pytest.fixture
def new_columnar_upload_file(session: SessionBase,
                             s3,
                             bucket,
                             new_session_upload):
    filename = "npcv1.csv"
    enumed_filetype = DataFile.DataFileType.Columnar
    url = "www.test_columnar_filename.com"

    file_key = 'npcv1.csv'
    s3.Object(bucket.name, file_key).upload_file('test_files/' + file_key)

    # new_columnar_uploadedFile = s3.Object(test_bucket.name, file_key)

    _new_raw_uploadFile = models_controller.add_upload_session_file(new_session_upload.id,
                                                                    filename=filename,
                                                                    filetype=enumed_filetype,
                                                                    url='uknown')

    return _new_raw_uploadFile


# def test_conversion_raw(session: SessionBase,
#                         s3,
#                         bucket,
#                         new_raw_uploaded_file):
#
#     session_upload = new_raw_uploaded_file.session
#
#     s3_raw_uploaded_file = s3.Object(bucket.name, new_raw_uploaded_file.filename)
#
#     dict_S3Metadata = {
#         'location': new_raw_uploaded_file.url,
#         'eTag': s3_raw_uploaded_file.e_tag,
#         'bucket': s3_raw_uploaded_file.bucket_name,
#         'key': s3_raw_uploaded_file.key,
#         'filetype': new_raw_uploaded_file.filetype
#     }
#
#     task = background_process_new_datafile.delay(dict_S3Metadata,
#                                                  session_upload.id,
#                                                  new_raw_uploaded_file.id)


def test_create_monkey_s3_object(session: SessionBase):
    new_bucket = aws.s3.Bucket.create('bucket')
    with open('test_files/hello.txt', 'rb') as data:
        aws.s3.Bucket(new_bucket.name).put_object(Key='hello.txt', Body=data)

    new_object = aws.s3.Object('bucket', 'hello.txt')
    assert new_object.bucket.name == 'bucket'
    assert new_object.key == 'hello.txt'


# def test_monkey_upload_file_to_s3(session: SessionBase):
#     new_bucket = aws.s3.Bucket.create('bucket')
#
#     with open('test_files/hello.txt', 'rb') as data:
#         aws.s3.Bucket(new_bucket.name).put_object(Key='hello.txt', Body=data)
#
#     new_object = aws.s3.Object('bucket', 'obj')
#
#     with open('test_files/hello.txt', 'rb') as data:
#         object.upload_fileobj(data)


def test_create_monkey_bucket_s3(session: SessionBase):
    new_bucket = aws.s3.Bucket.create('bucket')
    assert isinstance(new_bucket, MonkeyBucket)


def test_conversion_raw(session: SessionBase):
    new_bucket = aws.s3.Bucket.create('bucket')
    filename = 'hello.txt'

    with open('test_files/hello.txt', 'rb') as data:
        aws.s3.Bucket(new_bucket.name).put_object(Key='hello.txt', Body=data)
    s3_raw_uploaded_file = aws.s3.Object(new_bucket.name, filename)

    from taiga2.models import DataFile
    dict_S3Metadata = {
        'location': 'location',
        'eTag': 'eTag',
        'bucket': new_bucket.name,
        'key': s3_raw_uploaded_file.key,
        'filetype': DataFile.DataFileType.Raw.value
    }

    task = background_process_new_datafile.delay(dict_S3Metadata).wait()


def test_conversion_csv(session: SessionBase):
    new_bucket = aws.s3.Bucket.create('bucket')
    filename = 'npcv1.csv'

    with open('test_files/npcv1.csv', 'rb') as data:
        aws.s3.Bucket(new_bucket.name).put_object(Key='npcv1.csv', Body=data)
    s3_raw_uploaded_file = aws.s3.Object(new_bucket.name, filename)

    from taiga2.models import DataFile
    dict_S3Metadata = {
        'location': 'location',
        'eTag': 'eTag',
        'bucket': new_bucket.name,
        'key': s3_raw_uploaded_file.key,
        'filetype': DataFile.DataFileType.Columnar.value
    }

    task = background_process_new_datafile.delay(dict_S3Metadata).wait()




# @pytest.fixture
# @mock_s3
# def new_raw_upload_session_file(session: SessionBase,
#                      new_sessionUpload,
#                      new_raw_uploadFile,
#                      celery_worker):
#     # Upload to mock S3
#     # TODO: Pair with the aws.py
#     s3 = boto3.resource('s3')
#
#     bucket_name = 'test_bucket'
#     bucket = s3.Bucket('test_bucket').create()
#
#     file_key = 'hello.txt'
#     s3.Object(bucket_name, file_key).upload_file('test_files/hello.txt')
#
#     raw_uploadedFile = s3.Object(bucket_name, file_key)
#
#     # See swagger.yaml =>
#     # - location
#     # - eTag
#     # - bucket
#     # - key
#     # - filetype
#     dict_S3Metadata = {
#         'location': new_raw_uploadFile.location,
#         'eTag': raw_uploadedFile.e_tag,
#         'bucket': raw_uploadedFile.bucket_name,
#         'key': raw_uploadedFile.key,
#         'filetype': new_raw_uploadFile.filetype
#     }
#
#     json_task_id = endpoint.create_upload_session_file(dict_S3Metadata,
#                                             new_sessionUpload.id)
#
#     import json
#     result = background_process_new_datafile.AsyncResult(json.loads(json_task_id))
#
#     # Wait for the task to finish
#     result.get()


# def test_celery_print_config(session: SessionBase):
#     result = print_config.delay().wait()
#     assert result is None


# @mock_s3
# def test_add_new_raw_session_upload_file(session: SessionBase,
#                                          new_sessionUpload,
#                                          new_raw_upload_file):
#     s3 = boto3.resource('s3')
#
#     bucket_name = 'test_bucket'
#     bucket = s3.Bucket('test_bucket').create()
#
#     file_key = 'hello.txt'
#     s3.Object(bucket_name, file_key).upload_file('test_files/hello.txt')
#
#     raw_uploadedFile = s3.Object(bucket_name, file_key)
#
#     # See swagger.yaml =>
#     # - location
#     # - eTag
#     # - bucket
#     # - key
#     # - filetype
#     dict_S3Metadata = {
#         'location': new_raw_uploadFile.url,
#         'eTag': raw_uploadedFile.e_tag,
#         'bucket': raw_uploadedFile.bucket_name,
#         'key': raw_uploadedFile.key,
#         'filetype': new_raw_uploadFile.filetype.value
#     }
#
#     # json_task_id = endpoint.create_datafile(dict_S3Metadata,
#     #                                         new_sessionUpload.id)
#     #
#     # import json
#     # result = background_process_new_datafile.AsyncResult(json.loads(json_task_id))
#
#     # Wait for the task to finish
#     # result.get()
#
#     task = background_process_new_datafile.delay(dict_S3Metadata,
#                                                  new_sessionUpload.id,
#                                                  new_raw_uploadFile.id)
#
#     task_finished = task.wait()
#
#     # The datafile should not have been modified
#     assert

# @mock_s3
# def test_add_dataset_from_sessionUpload_raw_file(session: SessionBase,
#                                                  new_sessionUpload,
#                                                  new_raw_uploadFile,
#                                                  new_dummy_folder):
#     dataset_name = "Test dataset raw"
#     dataset_description = "Test dataset description raw"
#     dataset = models_controller.add_dataset_from_session(new_sessionUpload.id,
#                                                          dataset_name=dataset_name,
#                                                          dataset_description=dataset_description,
#                                                          current_folder_id=new_dummy_folder.id)
#     first_dataset_version = models_controller.get_dataset_versions(dataset.id)[0]
#
#     assert dataset_name == dataset.name
#     assert dataset_description == dataset.description
#     assert len(first_dataset_version.datafiles) != 0
#     assert first_dataset_version.datafiles[0].name == new_raw_uploadFile.filename

# @mock_s3
# def test_add_dataset_from_session_upload_columnar_file(session: SessionBase,
#                                                       new_sessionUpload,
#                                                       new_columnar_uploadFile,
#                                                       new_dummy_folder):
#     pass
    # dataset_name = "Test dataset raw"
    # dataset_description = "Test dataset description raw"
    # dataset = models_controller.add_dataset_from_session(new_sessionUpload.id,
    #                                                      dataset_name=dataset_name,
    #                                                      dataset_description=dataset_description,
    #                                                      current_folder_id=new_dummy_folder.id)
    # first_dataset_version = models_controller.get_dataset_versions(dataset.id)[0]
    #
    # assert dataset_name == dataset.name
    # assert dataset_description == dataset.description
    # assert len(first_dataset_version.datafiles) != 0
    # assert first_dataset_version.datafiles[0].name == new_raw_uploadFile.filename
