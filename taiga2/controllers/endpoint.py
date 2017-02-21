from flask import current_app, json
# TODO: Change the app containing db to api_app => current_app
import taiga2.controllers.models_controller as models_controller
import taiga2.schemas as schemas
import taiga2.conv as conversion
from taiga2.models import DataFile


import logging

log = logging.getLogger(__name__)

# Handle URL upload
from flask import render_template, request, redirect, url_for
import os, json

from taiga2.aws import aws
from taiga2.aws import sign_url as aws_sign_url

import flask

ADMIN_USER_ID = "admin"


def get_dataset(datasetId):
    dataset = models_controller.get_dataset(datasetId)
    if dataset is None:
        flask.abort(404)

    dataset_schema = schemas.DatasetSchema()
    json_dataset_data = dataset_schema.dump(dataset).data
    return flask.jsonify(json_dataset_data)


def create_folder(metadata):
    # TODO: Add the add_folder_entry inside the add_folder function?
    folder_name = metadata['name']
    folder_description = metadata['description']
    parent_id = metadata['parentId']


    # TODO: Instead of the string 'folder', use the model.Folder.FolderType.folder
    new_folder = models_controller.add_folder(name=folder_name,
                                              folder_type='folder',
                                              description=folder_description)
    models_controller.add_folder_entry(parent_id, new_folder.id)

    folder_named_id_schema = schemas.FolderNamedIdSchema()
    json_folder_named_id = folder_named_id_schema.dump(new_folder).data

    return flask.jsonify(json_folder_named_id)


def get_folder(folder_id):
    folder = models_controller.get_folder(folder_id)
    if folder is None:
        flask.abort(404)

    folder_schema = schemas.FolderSchema()
    json_data_folder = folder_schema.dump(folder).data
    return flask.jsonify(json_data_folder)


def update_folder_name(folderId, NameUpdate):
    updated_dataset = models_controller.update_folder_name(folderId, NameUpdate["name"])
    # TODO: Return the dataset id
    return flask.jsonify({})


def update_folder_description(folderId, DescriptionUpdate):
    models_controller.update_folder_description(folderId, DescriptionUpdate["description"])
    # TODO: Return the dataset id
    return flask.jsonify({})


def get_user():
    # We get the first user which should be Admin
    user = models_controller.get_current_session_user()
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


def get_dataset_first(dataset_id):
    first_dataset_version = models_controller.get_first_dataset_version(dataset_id)

    dataset_version_schema = schemas.DatasetVersionSummarySchema()
    json_data_first_dataset_version = dataset_version_schema.dump(first_dataset_version).data
    return flask.jsonify(json_data_first_dataset_version)


def update_dataset_name(datasetId, NameUpdate):
    updated_dataset = models_controller.update_dataset_name(datasetId, NameUpdate["name"])
    # TODO: Return the dataset id
    return flask.jsonify({})


def update_dataset_description(datasetId, DescriptionUpdate):
    models_controller.update_dataset_description(datasetId, DescriptionUpdate["description"])
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
#      location:
#      eTag:
#      bucket:
#      key:
#      filename:
#      filetype:

    s3_bucket = S3UploadedFileMetadata['bucket']

    initial_file_type = S3UploadedFileMetadata['filetype']
    initial_s3_key = S3UploadedFileMetadata['key']

    # Register this new file to the UploadSession received
    upload_session_file = models_controller.add_upload_session_file(session_id=sid,
                                                                    filename=S3UploadedFileMetadata['filename'],
                                                                    initial_file_type=initial_file_type,
                                                                    initial_s3_key=initial_s3_key,
                                                                    s3_bucket=s3_bucket)

    # Launch a Celery process to convert and get back to populate the db + send finish to client
    from taiga2.tasks import background_process_new_upload_session_file
    task = background_process_new_upload_session_file.delay(upload_session_file.id, initial_s3_key, initial_file_type, s3_bucket, upload_session_file.converted_s3_key)

    return flask.jsonify(task.id)


def create_new_upload_session():
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


def _no_transform_needed(requested_format, datafile_type):
    if requested_format == conversion.RAW_FORMAT and datafile_type == DataFile.DataFileType.Raw:
        return True

    if requested_format == conversion.HDF5_FORMAT and datafile_type == DataFile.DataFileType.HDF5:
        return True

    if requested_format == conversion.COLUMNAR_FORMAT and datafile_type == DataFile.DataFileType.Columnar:
        return True

    return False


def get_datafile(format, dataset_permaname=None, version=None, dataset_version_id=None, datafile_name=None, force=None):
    from taiga2.tasks import start_conversion_task

    datafile = models_controller.find_datafile(dataset_permaname, version, dataset_version_id, datafile_name)
    if datafile is None:
        flask.abort(404)

    dataset_version = datafile.dataset_version
    dataset_version_version = dataset_version.version
    dataset_version_id = dataset_version.id
    dataset_id = dataset_version.dataset.id
    datafile_name = datafile.name
    dataset_name = dataset_version.dataset.name
    dataset_permaname = dataset_version.dataset.permaname

    if format == "metadata":
        urls = None
        conversion_status = ""
    elif _no_transform_needed(format, datafile.type):
        # no conversion is necessary
        urls = [aws_sign_url(datafile.url)]
        conversion_status = ""
    else:
        force_conversion = force == "Y"
        is_new, entry = models_controller.get_conversion_cache_entry(dataset_version_id, datafile_name, format)

        from taiga2 import models
        if not is_new:
            if entry.state == models.ConversionEntryState.failed and not force_conversion:
                flask.abort(500) # report internal error
            elif not entry_is_valid(entry) or force_conversion:
                log.warning("Cache entry not associated with a running task, deleting to try again")
                models_controller.delete_conversion_cache_entry(entry.id)
                is_new, entry = models_controller.get_conversion_cache_entry(dataset_version_id, datafile_name, format)

        if is_new:
            log.error("endpoint %s %s", id(flask.g), dir(flask.g))
            t = start_conversion_task.delay(datafile.s3_bucket, datafile.s3_key, str(datafile.type), format, entry.id)
            log.error("ended %s %s", flask.g, dir(flask.g))
            models_controller.update_conversion_cache_entry_with_task_id(entry.id, t.id)

        urls = models_controller.get_signed_urls_from_cache_entry(entry.urls_as_json)
        conversion_status = entry.status

    result = dict(dataset_name=dataset_name,
                  dataset_permaname=dataset_permaname,
                  dataset_version=dataset_version_version,
                  dataset_id=dataset_id,
                  dataset_version_id=dataset_version_id,
                  datafile_name=datafile_name,
                  status=conversion_status)

    if urls is not None:
        result['urls'] = urls

    return flask.jsonify(result)


def entry_is_valid(entry):
    # while celery eager eval is enabled, we cannot use AsyncResult so just assume any existing
    # cache value is fine.
    if flask.current_app.config["TESTING"]:
        return True

    "make sure that either this entry resulted in a URL or is actively running now"
    from taiga2.tasks import start_conversion_task
    if entry.urls_as_json is not None:
        return True

    if entry.task_id is None:
        return False

    task = start_conversion_task.AsyncResult(entry.task_id)
    return task.state == 'PENDING'


def move_to_trash(entryIds):
    print("Just received the entries to throw into the bin: {}".format(entryIds))
    models_controller.move_to_trash(entryIds)

    return flask.jsonify({})
