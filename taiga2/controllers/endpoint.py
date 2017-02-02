from flask import current_app, json
# TODO: Change the app containing db to api_app => current_app
import taiga2.controllers.models_controller as models_controller
import taiga2.schemas as schemas

# Handle URL upload
from flask import render_template, request, redirect, url_for
import os, json

from taiga2.aws import aws
from uuid import uuid4

import flask
import time
import enum

ADMIN_USER_ID = "admin"


def get_dataset(datasetId):
    dataset = models_controller.get_dataset(datasetId)
    if dataset is None:
        flask.abort(404)

    dataset_schema = schemas.DatasetSchema()
    json_dataset_data = dataset_schema.dump(dataset).data
    return flask.jsonify(json_dataset_data)


def get_folder(folder_id):
    folder = models_controller.get_folder(folder_id)
    if folder is None:
        flask.abort(404)

    folder_schema = schemas.FolderSchema()
    json_data_folder = folder_schema.dump(folder).data
    return flask.jsonify(json_data_folder)


def _get_user_id():
    return ADMIN_USER_ID


# TODO: Should never be used in production!
# TODO: Should implement a get_user(uuid) or get_user(name)
def get_user():
    # We get the first user which should be Admin
    user = models_controller._get_test_user()
    user_schema = schemas.UserSchema()
    json_data_user = user_schema.dump(user).data

    return flask.jsonify(json_data_user)


def get_s3_credentials():
    """
    Create an access token to access S3 using the ~/.aws/credentials information
    :return: S3Credentials
    """
    expires_in = flask.current_app.config.get("CLIENT_UPLOAD_TOKEN_EXPIRY", 900)

    sts = aws.client_upload_sts

    temporary_session_credentials = sts.get_session_token(
        DurationSeconds=expires_in
    )

    dict_credentials = temporary_session_credentials['Credentials']

    bucket = flask.current_app.config["S3_BUCKET"]
    prefix = flask.current_app.config.get("S3_PREFIX", "upload/")

    model_frontend_credentials = {
        'accessKeyId': dict_credentials['AccessKeyId'],
        'expiration': dict_credentials['Expiration'],
        'secretAccessKey': dict_credentials['SecretAccessKey'],
        'sessionToken': dict_credentials['SessionToken'],
        'bucket': bucket,
        'prefix': prefix
    }

    # See frontend/models/models.ts for the S3Credentials object and Swagger.yaml
    return flask.jsonify(model_frontend_credentials)


def create_folder(metadata):
    # TODO: Add the add_folder_entry inside the add_folder function?
    folder_name = metadata['name']
    folder_description = metadata['description']
    parent_id = metadata['parent']

    folder_id = models_controller.add_folder(folder_name, 'folder', folder_description)
    models_controller.add_folder_entry(parent_id, folder_id, 'folder')

    return flask.jsonify(id=folder_id, name=metadata['name'])


def get_dataset_first(dataset_id):
    first_dataset_version = models_controller.get_first_dataset_version(dataset_id)

    dataset_version_schema = schemas.DatasetVersionSummarySchema()
    json_data_first_dataset_version = dataset_version_schema.dump(first_dataset_version).data
    return flask.jsonify(json_data_first_dataset_version)


def update_dataset_name(datasetId, NameUpdate):
    updated_dataset = models_controller.update_dataset_name(_get_user_id(), datasetId, NameUpdate["name"])
    # TODO: Return the dataset id
    return flask.jsonify({})


def update_dataset_description(datasetId, DescriptionUpdate):
    models_controller.update_dataset_description(_get_user_id(), datasetId, DescriptionUpdate["description"])
    # TODO: Return the dataset id
    return flask.jsonify({})


def get_dataset_version(datasetVersion_id):
    dv = models_controller.get_dataset_version(dataset_version_id=datasetVersion_id)
    if dv is None:
        flask.abort(404)

    dataset_version_schema = schemas.DatasetVersionSchema()
    json_dv_data = dataset_version_schema.dump(dv).data

    return flask.jsonify(json_dv_data)


def get_dataset_version_from_dataset(datasetId, datasetVersionId):
    dataset_version_schema = schemas.DatasetVersionSchema()
    dataset_schema = schemas.DatasetSchema()

    dataset_version = models_controller \
        .get_dataset_version_by_dataset_id_and_dataset_version_id(datasetId,
                                                                  datasetVersionId)
    dataset = dataset_version.dataset

    json_dv_data = dataset_version_schema.dump(dataset_version).data
    json_dataset_data = dataset_schema.dump(dataset).data

    # Preparation of the dictonary to return both objects
    json_dv_and_dataset_data = {'datasetVersion': json_dv_data, 'dataset': json_dataset_data}

    return flask.jsonify(json_dv_and_dataset_data)


def create_upload_session_file(S3UploadedFileMetadata, sid):

    # TODO: We should first check the file exists before adding it in the db
    # TODO: We could also check the type of the object
    # TODO: We need to make a distinction between numerical or table data
    # TODO: Add also Parquet file conversion

    # Register this new file to the UploadSession received
    upload_session_file = models_controller.add_upload_session_file(session_id=sid,
                                                                    filename=S3UploadedFileMetadata['filename'],
                                                                    filetype=S3UploadedFileMetadata['filetype'],
                                                                    url=S3UploadedFileMetadata['location'],
                                                                    s3_bucket=S3UploadedFileMetadata['bucket'])

    convert_key = upload_session_file.converted_s3_key

    # Launch a Celery process to convert and get back to populate the db + send finish to client
    from taiga2.tasks import background_process_new_upload_session_file, update_session_file_converted_type
    task = background_process_new_upload_session_file \
        .apply_async((S3UploadedFileMetadata, convert_key),
                     link=update_session_file_converted_type.s(upload_session_file.id))

    # We need to update the uploadSession with the return of the background_process

    return flask.jsonify(task.id)


def create_new_upload_session():
    # TODO: Add the user_id related to this new session
    upload_session = models_controller.add_new_upload_session(0)
    return flask.jsonify(upload_session.id)


def create_dataset(sessionDatasetInfo):
    session_id = sessionDatasetInfo['sessionId']
    dataset_name = sessionDatasetInfo['datasetName']
    dataset_description = sessionDatasetInfo['datasetDescription']
    current_folder_id = sessionDatasetInfo['currentFolderId']

    added_dataset = models_controller.add_dataset_from_session(session_id,
                                                               dataset_name,
                                                               dataset_description,
                                                               current_folder_id)

    return flask.jsonify(added_dataset.id)


def task_status(taskStatusId):
    from taiga2.tasks import taskstatus
    status = taskstatus(taskStatusId)
    return flask.jsonify(status)

import taiga2.conv as conversion
from taiga2.models import DataFile

def get_datafile(dataset_version_id, name, format):
    from taiga2.tasks import start_conversion_task

    datafile = models_controller.get_datafile_by_version_and_name(dataset_version_id, name)
    if datafile is None:
        flask.abort(404)

    dataset_version = datafile.dataset_version
    dataset_version_id = dataset_version.id
    dataset_id = dataset_version.dataset.id
    datafile_name = datafile.name

    if format == conversion.RAW_FORMAT and datafile.type == DataFile.DataFileType:
        # no conversion is necessary
        urls = [aws.sign_url(datafile.url)]
    else:
        is_new, entry = models_controller.get_conversion_cache_entry(dataset_version_id, datafile_name, format)

        if is_new:
            start_conversion_task(datafile.url, datafile.type, format, entry.id)
        urls = models_controller.get_signed_urls_from_cache_entry(entry.urls_as_json)

    result = dict(dataset_id=dataset_id,
                  dataset_version_id=dataset_version_id,
                  datafile_name=datafile_name,
                  urls=urls,
                  status=entry.status)

    print("result:", repr(result))

    return flask.jsonify(result)