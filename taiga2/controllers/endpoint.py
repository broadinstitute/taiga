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

ADMIN_USER_ID = "admin"

def get_dataset(datasetId):
    dataset = models_controller.get_dataset(datasetId)
    if dataset is None:
        flask.abort(404)

    dataset_schema = schemas.DatasetSchema()
    json_dataset_data = dataset_schema.dump(dataset).data
    return flask.jsonify(json_dataset_data)


def get_folder(folder_id):
    print("get_folder start", time.asctime())
    folder = models_controller.get_folder(folder_id)
    if folder is None:
        flask.abort(404)

    folder_schema = schemas.FolderSchema()
    json_data_folder = folder_schema.dump(folder).data
    print("get_folder stop", time.asctime())
    return flask.jsonify(json_data_folder)


def _get_user_id():
    return ADMIN_USER_ID


def get_user():
    user = models_controller.get_user(1)
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

    # See frontend/models/models.ts for the S3Credentials object
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
    first_dataset_version = models_controller.get_first_dataset_version(int(dataset_id))

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
    dv = models_controller.get_dataset_version(dataset_version_id=int(datasetVersion_id))
    if dv is None:
        flask.abort(404)

    dataset_version_schema = schemas.DatasetVersionSchema()
    json_dv_data = dataset_version_schema.dump(dv).data

    return flask.jsonify(json_dv_data)


def create_datafile(S3UploadedFileMetadata, sid):

    # TODO: We should first check the file exists before adding it in the db
    # TODO: We could also check the type of the object
    # TODO: We need to make a distinction between numerical or table data
    # TODO: Add also Parquet file conversion

    # Register this new file to the UploadSession received
    upload_session_file = models_controller.add_upload_session_file(sid,
                                                                    S3UploadedFileMetadata['key'],
                                                                    S3UploadedFileMetadata['filetype'],
                                                                    S3UploadedFileMetadata['location'])

    # Launch a Celery process to convert and get back to populate the db + send finish to client
    from taiga2.tasks import background_process_new_datafile
    task = background_process_new_datafile.delay(S3UploadedFileMetadata, sid, upload_session_file.id)

    return flask.jsonify(task.id)


def create_new_upload_session():
    # TODO: Add the user_id related to this new session
    upload_session = models_controller.add_new_upload_session()
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


def get_datafile(q, format):
    from taiga2.tasks import taskstatus

    datafile = models_controller.resolve_to_datafile(q)

    dataset_id = datafile.version.dataset.id
    dataset_version_id = datafile.version
    datafile_name = datafile.name

    is_new, entry = models_controller.get_conversion_cache_entry(dataset_version_id, datafile_name, format)

    if is_new:
        data_file = get_datafile(dataset_version_id, datafile_name)
        start_conversion_task(data_file.url, data_file.format, format, entry.id)

    result = dict(dataset_id=dataset_id,
                  dataset_version_id=dataset_version_id,
                  datafile_name=datafile_name,
                  urls=models_controller.get_signed_urls_from_cache_entry(entry),
                  status=entry.status)

    return flask.jsonify(result)