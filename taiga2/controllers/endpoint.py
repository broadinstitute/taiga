import flask
import logging
import sys
import time
import re
from io import BytesIO
from taiga2.dataset_subscriptions import send_emails_for_dataset

from .endpoint_validation import validate

from sqlalchemy.orm.exc import NoResultFound
from google.cloud import storage, exceptions as gcs_exceptions
from requests.exceptions import HTTPError

# TODO: Change the app containing db to api_app => current_app
from taiga2.controllers import models_controller
import taiga2.schemas as schemas
import taiga2.conv as conversion
from taiga2.models import (
    Activity,
    DatasetVersion,
    EntryRightsEnum,
    VersionAdditionActivity,
    DataFile,
    GCSObjectDataFile,
    normalize_name,
    SearchResult,
)
from taiga2.models import S3DataFile

from taiga2.third_party_clients.aws import (
    aws,
    create_signed_get_obj,
    create_s3_url as aws_create_s3_url,
)

from taiga2.third_party_clients.gcs import (
    get_blob,
    parse_gcs_path,
    create_signed_gcs_url,
)
import taiga2.third_party_clients.figshare as figshare

log = logging.getLogger(__name__)

# Handle URL upload
import json

from connexion.exceptions import ProblemException

ADMIN_USER_ID = "admin"


def api_error(msg):
    raise ProblemException(detail=msg)


@validate
def get_dataset(datasetId):
    # TODO: We could receive a datasetId being a permaname. This is not good as our function is not respecting the atomicity. Should handle the usage of a different function if permaname
    # try using ID
    dataset = models_controller.get_dataset(datasetId, one_or_none=True)

    # if that failed, try by permaname
    if dataset is None:
        dataset = models_controller.get_dataset_from_permaname(
            datasetId, one_or_none=True
        )

    if dataset is None:
        flask.abort(404)

    # TODO: We should instead check in the controller, but did not want to repeat
    # Remove folders that are not allowed to be seen
    allowed_dataset = dataset
    allowed_dataset.parents = models_controller.filter_allowed_parents(dataset.parents)
    last_dataset_version = models_controller.get_latest_dataset_version(
        allowed_dataset.id
    )
    allowed_dataset.description = last_dataset_version.description

    # Get the rights of the user over the folder
    right = models_controller.get_rights(dataset.id)
    dataset_schema = schemas.DatasetSchema()
    print("The right is: {}".format(right))
    dataset_schema.context["entry_user_right"] = right
    subscription = models_controller.get_dataset_subscription_for_dataset_and_user(
        dataset.id
    )
    dataset_schema.context["subscription_id"] = (
        subscription.id if subscription is not None else None
    )
    json_dataset_data = dataset_schema.dump(allowed_dataset).data
    return flask.jsonify(json_dataset_data)


@validate
def get_datasets(datasetIdsDict):
    array_dataset_ids = datasetIdsDict["datasetIds"]

    start_time = time.time()
    datasets = models_controller.get_datasets(array_dataset_ids)
    elapsed_time = time.time() - start_time
    print("Time to get all the datasets: {}".format(elapsed_time))

    start_time = time.time()
    dataset_schema = schemas.DatasetFullSchema(many=True)
    json_data_datasets = dataset_schema.dump(datasets).data
    elapsed_time = time.time() - start_time
    print("Time to dump all the datasets via Marshmallow: {}".format(elapsed_time))

    return flask.jsonify(json_data_datasets)


@validate
def create_folder(metadata):
    """Create a folder given a metadata dictionary of this form:
    metadata['name'], metadata['description'], metadata['parentId']"""
    # TODO: Add the add_folder_entry inside the add_folder function?
    folder_name = metadata["name"]
    folder_description = metadata["description"]
    parent_id = metadata["parentId"]

    new_folder = models_controller.add_folder(
        name=folder_name,
        folder_type=models_controller.Folder.FolderType.folder,
        description=folder_description,
    )
    models_controller.add_folder_entry(parent_id, new_folder.id)

    folder_named_id_schema = schemas.FolderNamedIdSchema()
    json_folder_named_id = folder_named_id_schema.dump(new_folder).data

    return flask.jsonify(json_folder_named_id)


# @validate commented out because some creators are null and swagger doesn't seem to allow optional props at the top level
def get_folder(folder_id):
    folder = models_controller.get_folder(folder_id, one_or_none=True)
    if folder is None:
        flask.abort(404)

    folder.parents = models_controller.filter_allowed_parents(folder.parents)

    # Get the rights of the user over the folder
    right = models_controller.get_rights(folder_id)

    folder_schema = schemas.FolderSchema()
    folder_schema.context["entry_user_right"] = right
    json_data_folder = folder_schema.dump(folder).data

    return flask.jsonify(json_data_folder)


@validate
def update_folder_name(folderId, NameUpdate):
    updated_folder = models_controller.update_folder_name(folderId, NameUpdate["name"])

    return flask.jsonify(updated_folder.id)


@validate
def update_folder_description(folderId, DescriptionUpdate):
    updated_folder = models_controller.update_folder_description(
        folderId, DescriptionUpdate["description"]
    )

    return flask.jsonify(updated_folder.id)


@validate
def get_user():
    # We get the first user which should be Admin
    user = models_controller.get_current_session_user()
    user_schema = schemas.UserSchema()
    json_data_user = user_schema.dump(user).data

    return flask.jsonify(json_data_user)


@validate
def get_all_users():
    all_users = models_controller.get_all_users()
    users_schema = schemas.UserSchema(many=True)
    json_data_user = users_schema.dump(all_users).data

    return flask.jsonify(json_data_user)


@validate
def get_s3_credentials():
    """
    Create an access token to access S3 using the ~/.aws/credentials information
    :return: S3Credentials
    """
    expires_in = flask.current_app.config.get("CLIENT_UPLOAD_TOKEN_EXPIRY", 900)

    sts = aws.client_upload_sts

    temporary_session_credentials = sts.get_session_token(DurationSeconds=expires_in)

    dict_credentials = temporary_session_credentials["Credentials"]

    bucket = flask.current_app.config["S3_BUCKET"]
    prefix = flask.current_app.config.get("S3_PREFIX", "upload/")

    model_frontend_credentials = {
        "accessKeyId": dict_credentials["AccessKeyId"],
        "expiration": dict_credentials["Expiration"],
        "secretAccessKey": dict_credentials["SecretAccessKey"],
        "sessionToken": dict_credentials["SessionToken"],
        "bucket": bucket,
        "prefix": prefix,
    }

    # See frontend/models/models.ts for the S3Credentials object and Swagger.yaml
    return flask.jsonify(model_frontend_credentials)


# TODO: Use for every DatasetVersionSchema?
def get_dataset_version_schema_json(
    dataset_version: DatasetVersion, dataset_version_right: EntryRightsEnum
):
    dataset_version_schema = schemas.DatasetVersionSchema()
    dataset_version_schema.context["entry_user_right"] = dataset_version_right

    if dataset_version.figshare_dataset_version_link is not None:
        try:
            figshare_article_info = figshare.get_article_information(
                dataset_version.figshare_dataset_version_link
            )
            dataset_version_schema.context["figshare"] = figshare_article_info
        except:
            pass

    return dataset_version_schema.dump(dataset_version).data


@validate
def get_dataset_last(dataset_id):
    last_dataset_version = models_controller.get_latest_dataset_version(dataset_id)

    right = models_controller.get_rights(last_dataset_version.id)

    json_data_first_dataset_version = get_dataset_version_schema_json(
        last_dataset_version, right
    )
    return flask.jsonify(json_data_first_dataset_version)


@validate
def update_dataset_name(datasetId, NameUpdate):
    updated_dataset = models_controller.update_dataset_name(
        datasetId, NameUpdate["name"]
    )

    return flask.jsonify(updated_dataset.id)


@validate
def update_dataset_description(datasetId, DescriptionUpdate):
    last_dataset_version = models_controller.get_latest_dataset_version(datasetId)
    updated_dataset = models_controller.update_dataset_version_description(
        last_dataset_version.id, DescriptionUpdate["description"]
    )

    return flask.jsonify(updated_dataset.dataset_id)


@validate
def create_or_update_dataset_access_log(datasetId):
    access_log = models_controller.add_or_update_dataset_access_log(datasetId)
    return flask.jsonify(access_log.id)


@validate
def get_datasets_access_logs():
    array_access_logs = models_controller.get_datasets_access_logs()

    access_log_schema = schemas.AccessLogSchema(many=True)
    json_data_access_logs_current_user_datasets = access_log_schema.dump(
        array_access_logs
    ).data

    return flask.jsonify(json_data_access_logs_current_user_datasets)


@validate
def get_entry_access_logs(entryId):
    array_access_logs = models_controller.get_entry_access_logs(entryId)

    access_log_schema = schemas.AccessLogSchema(many=True)
    json_data_access_logs_entry = access_log_schema.dump(array_access_logs).data

    return flask.jsonify(json_data_access_logs_entry)


@validate
def get_entries_access_logs():
    array_access_logs = models_controller.get_entries_access_logs()

    access_log_schema = schemas.AccessLogSchema(many=True)
    json_data_access_logs_current_user_entries = access_log_schema.dump(
        array_access_logs
    ).data

    return flask.jsonify(json_data_access_logs_current_user_entries)


# @validate the swagger is wrong
def accessLogs_remove(accessLogsToRemove):
    models_controller.remove_accessLogs(accessLogsToRemove)
    return flask.jsonify({})


@validate
def create_or_update_entry_access_log(entryId):
    models_controller.add_or_update_entry_access_log(entryId)
    return flask.jsonify({})


@validate
def get_dataset_version(datasetVersion_id):
    dv = models_controller.get_dataset_version(
        dataset_version_id=datasetVersion_id, one_or_none=True
    )
    if dv is None:
        flask.abort(404)

    dataset_version_right = models_controller.get_rights(dv.id)

    dataset_version_schema = schemas.DatasetVersionSchema()
    dataset_version_schema.context["entry_user_right"] = dataset_version_right
    json_dv_data = dataset_version_schema.dump(dv).data

    return flask.jsonify(json_dv_data)


@validate
def get_dataset_versions(datasetVersionIdsDict):
    array_dataset_version_ids = datasetVersionIdsDict["datasetVersionIds"]
    dataset_versions = models_controller.get_dataset_versions_bulk(
        array_dataset_version_ids
    )

    dataset_version_schema = schemas.DatasetVersionSchema(many=True)

    # TODO: IMPORTANT and bug potential => Manage here the missing context depending on the dataset_v
    dataset_version_schema.context[
        "entry_user_right"
    ] = models_controller.EntryRightsEnum.can_view

    json_data_dataset_versions = dataset_version_schema.dump(dataset_versions).data

    return flask.jsonify(json_data_dataset_versions)


@validate
def get_dataset_version_from_dataset(datasetId, datasetVersionId):

    dataset_version = models_controller.get_dataset_version_by_dataset_id_and_dataset_version_id(
        datasetId, datasetVersionId, one_or_none=True
    )
    if dataset_version is None:
        # if we couldn't find a version by dataset_version_id, try permaname and version number.
        version_number = None
        try:
            version_number = int(datasetVersionId)
        except ValueError:
            # TODO: Log the error
            pass

        if version_number is not None:
            dataset_version = models_controller.get_dataset_version_by_permaname_and_version(
                datasetId, version_number, one_or_none=True
            )
        else:
            dataset_version = models_controller.get_latest_dataset_version_by_permaname(
                datasetId
            )

    if dataset_version is None:
        flask.abort(404)

    dataset_version_right = models_controller.get_rights(dataset_version.id)

    dataset = dataset_version.dataset
    dataset_right = models_controller.get_rights(dataset.id)

    dataset.parents = models_controller.filter_allowed_parents(dataset.parents)
    dataset.description = dataset_version.description

    json_dv_data = get_dataset_version_schema_json(
        dataset_version, dataset_version_right
    )

    dataset_schema = schemas.DatasetSchema()
    dataset_schema.context["entry_user_right"] = dataset_right
    subscription = models_controller.get_dataset_subscription_for_dataset_and_user(
        dataset_version.dataset_id
    )
    dataset_schema.context["subscription_id"] = (
        subscription.id if subscription is not None else None
    )
    json_dataset_data = dataset_schema.dump(dataset).data

    # Preparation of the dictonary to return both objects
    json_dv_and_dataset_data = {
        "datasetVersion": json_dv_data,
        "dataset": json_dataset_data,
    }

    return flask.jsonify(json_dv_and_dataset_data)


@validate
def update_dataset_version_description(datasetVersionId, DescriptionUpdate):
    models_controller.update_dataset_version_description(
        datasetVersionId, DescriptionUpdate["description"]
    )
    return flask.jsonify({})


@validate
def deprecate_dataset_version(datasetVersionId, deprecationReasonObj):
    reason = deprecationReasonObj["deprecationReason"]

    try:
        models_controller.deprecate_dataset_version(datasetVersionId, reason)
    # TODO: Manage case by case exceptions => NotFound for example
    except:
        error = sys.exc_info()[1]
        flask.abort(500, "Error in deprecate_dataset_version: {}".format(error))

    return flask.jsonify({})


@validate
def de_deprecate_dataset_version(datasetVersionId):
    try:
        models_controller.approve_dataset_version(datasetVersionId)
    # TODO: Manage case by case exceptions => NotFound for example
    except:
        error = sys.exc_info()[0]
        flask.abort(500, "Error in approve_dataset_version: {}".format(error))

    return flask.jsonify({})


@validate
def delete_dataset_version(datasetVersionId):
    # TODO: Manage errors to let the user know
    new_state = models_controller.delete_dataset_version(
        dataset_version_id=datasetVersionId
    )

    return flask.jsonify({})


def de_delete_dataset_version(datasetVersionId):
    new_state = models_controller.deprecate_dataset_version_from_delete_state(
        dataset_version_id=datasetVersionId
    )

    return flask.jsonify({})


from .models_controller import (
    InvalidTaigaIdFormat,
    get_current_session_user,
    log_datafile_read_access_info,
)


@validate
def create_upload_session_file(uploadMetadata, sid):
    filename = uploadMetadata["filename"]
    if uploadMetadata["filetype"] == "s3":
        S3UploadedFileMetadata = uploadMetadata["s3Upload"]
        s3_bucket = S3UploadedFileMetadata["bucket"]

        initial_file_type = S3UploadedFileMetadata["format"]
        initial_s3_key = S3UploadedFileMetadata["key"]

        encoding = S3UploadedFileMetadata.get("encoding")

        # Register this new file to the UploadSession received
        upload_session_file = models_controller.add_upload_session_s3_file(
            session_id=sid,
            filename=filename,
            initial_file_type=initial_file_type,
            initial_s3_key=initial_s3_key,
            s3_bucket=s3_bucket,
            encoding=encoding,
        )

        # Launch a Celery process to convert and get back to populate the db + send finish to client
        from taiga2.tasks import background_process_new_upload_session_file

        task = background_process_new_upload_session_file.delay(
            upload_session_file.id,
            initial_s3_key,
            initial_file_type,
            s3_bucket,
            upload_session_file.converted_s3_key,
            upload_session_file.compressed_s3_key,
            upload_session_file.encoding,
        )

        return flask.jsonify(task.id)
    elif uploadMetadata["filetype"] == "virtual":
        existing_taiga_id = uploadMetadata["existingTaigaId"]

        try:
            data_file = models_controller.get_datafile_by_taiga_id(
                existing_taiga_id, one_or_none=True
            )
        except InvalidTaigaIdFormat as ex:
            api_error(
                "The following was not formatted like a valid taiga ID: {}".format(
                    ex.taiga_id
                )
            )

        if data_file is None:
            api_error("Unknown taiga ID: " + existing_taiga_id)

        models_controller.add_upload_session_virtual_file(
            session_id=sid, filename=filename, data_file_id=data_file.id
        )

        return flask.jsonify("done")
    elif uploadMetadata["filetype"] == "gcs":
        gcs_path = uploadMetadata["gcsPath"]

        if gcs_path is None:
            api_error("No GCS path given")

        try:
            bucket_name, object_name = parse_gcs_path(gcs_path)
            blob = get_blob(bucket_name, object_name)
        except ValueError as e:
            api_error(str(e))

        if not blob:
            api_error("No object found: {}".format(object_name))

        generation_id = blob.generation

        models_controller.add_upload_session_gcs_file(
            session_id=sid,
            filename=filename,
            gcs_path=gcs_path,
            generation_id=str(generation_id),
        )

        return flask.jsonify("done")
    else:
        api_error(
            "unknown filetype " + uploadMetadata["filetype"] + ", expected '' or ''"
        )


@validate
def create_new_upload_session():
    upload_session = models_controller.add_new_upload_session()
    return flask.jsonify(upload_session.id)


def _find_data_file_id(data_file_id):
    "given a data file id of the form <dataset-permaname>.<version>/<filename> return the internal file id"
    m = re.match("([a-zA-Z0-9-]+)\\.([0-9]+)/(.*)", data_file_id)
    if m is None:
        return None
    permaname = m.group(1)
    version = int(m.group(2))
    filename = m.group(3)

    version = models_controller.get_dataset_version_by_permaname_and_version(
        permaname, version, True
    )
    if version is None:
        return None

    data_file = models_controller.get_datafile_by_version_and_name(
        version.id, filename, one_or_none=True
    )
    if data_file is None:
        return None

    return data_file.id


def _parse_data_file_aliases(files):
    result = []
    for file in files:
        orig_file_id = file["datafile"]
        data_file_id = _find_data_file_id(orig_file_id)
        if data_file_id is None:
            raise Exception("Could not find data file for {}".format(orig_file_id))
        result.append(
            models_controller.DataFileAlias(
                name=file["name"], data_file_id=data_file_id
            )
        )
    return result


@validate
def create_dataset(sessionDatasetInfo):
    session_id = sessionDatasetInfo["sessionId"]
    dataset_name = sessionDatasetInfo["datasetName"]
    dataset_description = sessionDatasetInfo.get("datasetDescription", None)
    current_folder_id = sessionDatasetInfo["currentFolderId"]

    added_dataset = models_controller.add_dataset_from_session(
        session_id, dataset_name, dataset_description, current_folder_id
    )

    return flask.jsonify(added_dataset.id)


def _create_new_dataset_version_from_session(
    session_id,
    dataset_id,
    dataset_version,
    new_description,
    changes_description,
    add_existing_files,
):
    if add_existing_files:
        all_datafiles = models_controller.get_session_files_including_existing_files(
            session_id, dataset_version, dataset_id
        )
    else:
        all_datafiles = models_controller.add_datafiles_from_session(session_id)

    all_datafile_ids = [datafile.id for datafile in all_datafiles]

    new_dataset_version = models_controller.add_dataset_version(
        dataset_id=dataset_id,
        datafiles_ids=all_datafile_ids,
        new_description=new_description,
        changes_description=changes_description,
    )

    return new_dataset_version


def _handle_version_addition_activity(
    current_user, dataset_id, new_description, new_dataset_version
):

    (
        comments,
        latest_dataset_version,
    ) = models_controller.get_comments_and_latest_dataset_version(
        dataset_id, new_dataset_version.datafiles
    )

    activity = VersionAdditionActivity(
        user_id=current_user.id,
        dataset_id=new_dataset_version.dataset_id,
        type=Activity.ActivityType.added_version,
        dataset_description=new_description
        if new_description != latest_dataset_version.description
        else None,
        dataset_version=new_dataset_version.version,
        comments=comments,
    )
    models_controller.add_version_addition_activity(activity)

    dataset_subscriptions = models_controller.get_dataset_subscriptions_for_dataset(
        dataset_id
    )
    if not any(ds.user_id == current_user.id for ds in dataset_subscriptions):
        add_dataset_subscription(dataset_id)
    send_emails_for_dataset(dataset_id, current_user.id)

    return new_dataset_version


@validate
def create_new_dataset_version(datasetVersionMetadata):
    assert "datafileIds" not in datasetVersionMetadata
    session_id = datasetVersionMetadata["sessionId"]
    dataset_id = datasetVersionMetadata["datasetId"]
    new_description = datasetVersionMetadata["newDescription"]
    changes_description = datasetVersionMetadata.get("changesDescription", None)

    # Older versions of taigapy don't include add_existing_files in the params. Instead,
    # add_existing_files is handled within the taigapy logic. So it's safe to default this
    # to False and avoid repeating this logic.
    add_existing_files = datasetVersionMetadata.get("addExistingFiles", False)

    # Only used if add_existing_files is True to support grabbing the existing files
    dataset_version = datasetVersionMetadata.get("datasetVersion", None)
    current_user = models_controller.get_current_session_user()

    models_controller.lock()

    new_dataset_version = _create_new_dataset_version_from_session(
        session_id,
        dataset_id,
        dataset_version,
        new_description,
        changes_description,
        add_existing_files,
    )

    _handle_version_addition_activity(
        current_user, dataset_id, new_description, new_dataset_version
    )

    return flask.jsonify(new_dataset_version.id)


@validate
def task_status(taskStatusId):
    from taiga2.tasks import taskstatus

    status = taskstatus(taskStatusId)
    return flask.jsonify(status)


def _no_transform_needed(requested_format, datafile_type):
    if (
        requested_format == conversion.RAW_FORMAT
        and datafile_type == S3DataFile.DataFileFormat.Raw
    ):
        return True

    if (
        requested_format == conversion.HDF5_FORMAT
        and datafile_type == S3DataFile.DataFileFormat.HDF5
    ):
        return True

    if (
        requested_format == conversion.COLUMNAR_FORMAT
        and datafile_type == S3DataFile.DataFileFormat.Columnar
    ):
        return True

    return False


def _make_dl_name(datafile_name, dataset_version_version, dataset_name, format):
    if format != "raw":
        suffix = "." + format
    else:
        suffix = ""

    name = "{}_v{}-{}{}".format(
        normalize_name(dataset_name),
        dataset_version_version,
        normalize_name(datafile_name),
        suffix,
    )
    return name


def _get_gcs_datafile(
    real_datafile,
    datafile,
    dataset_version,
    dataset_version_version,
    dataset_version_id,
    dataset_id,
    datafile_name,
    dataset_name,
    dataset_permaname,
    format,
):
    if format == "metadata":
        urls = None
        conversion_status = "Completed successfully"
    else:
        # no conversion is necessary
        bucket_name, object_name = parse_gcs_path(real_datafile.gcs_path)
        urls = [create_signed_gcs_url(bucket_name, object_name)]
        conversion_status = "Completed successfully"

    # TODO: This should be handled by a Marshmallow schema and not created on the fly
    result = dict(
        dataset_name=dataset_name,
        dataset_permaname=dataset_permaname,
        dataset_version=str(dataset_version_version),
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        datafile_name=datafile_name,
        status=conversion_status,
        state=dataset_version.state.value,
        reason_state=dataset_version.reason_state,
        datafile_type=datafile.type,
        gcs_path=real_datafile.gcs_path,
    )

    if urls is not None:
        result["urls"] = urls

    if datafile.type == "virtual":
        result["underlying_file_id"] = datafile.underlying_file_id

    return result


def _get_s3_datafile(
    real_datafile,
    datafile,
    dataset_version,
    dataset_version_version,
    dataset_version_id,
    dataset_id,
    datafile_name,
    dataset_name,
    dataset_permaname,
    dl_filename,
    force,
    format,
):
    from taiga2.tasks import start_conversion_task

    if format == "metadata":
        urls = None
        conversion_status = "Completed successfully"
    elif _no_transform_needed(format, real_datafile.format):
        # no conversion is necessary
        urls = [
            create_signed_get_obj(
                real_datafile.s3_bucket, real_datafile.s3_key, dl_filename
            )
        ]
        conversion_status = "Completed successfully"
    elif format == conversion.COMPRESSED_FORMAT:
        if real_datafile.compressed_s3_key is None:
            return _backfill_compressed_file(real_datafile.id)

        obj = aws.s3.Object(real_datafile.s3_bucket, real_datafile.compressed_s3_key)

        new_format = format
        if "text/csv" in obj.content_type:
            new_format = "csv"
        elif "text/tab-separated-values" in obj.content_type:
            new_format = "tsv"

        dl_filename = _make_dl_name(
            datafile_name, dataset_version_version, dataset_name, new_format
        )

        urls = [
            create_signed_get_obj(
                real_datafile.s3_bucket, real_datafile.compressed_s3_key, dl_filename
            )
        ]
        conversion_status = "Completed successfully"
    else:
        force_conversion = force == "Y"
        is_new, entry = models_controller.get_conversion_cache_entry(
            real_datafile.dataset_version.id, real_datafile.name, format
        )

        from taiga2 import models

        if not is_new:
            if (
                entry.state == models.ConversionEntryState.failed
                and not force_conversion
            ):
                log.error(
                    "For entry {}, entry.state is failed and force_conversion is not set."
                    "Reporting internal error.".format(entry.id)
                )
                flask.abort(500)  # report internal error
            elif not entry_is_valid(entry) or force_conversion:
                log.warning(
                    "Cache entry not associated with a running task, deleting to try again"
                )
                models_controller.delete_conversion_cache_entry(entry.id)
                is_new, entry = models_controller.get_conversion_cache_entry(
                    real_datafile.dataset_version.id, real_datafile.name, format
                )

        if is_new:
            t = start_conversion_task.delay(
                real_datafile.s3_bucket,
                real_datafile.s3_key,
                str(real_datafile.format),
                format,
                entry.id,
            )
            models_controller.update_conversion_cache_entry_with_task_id(entry.id, t.id)

        urls = models_controller.get_signed_urls_from_cache_entry(
            entry.urls_as_json, dl_filename
        )
        conversion_status = entry.status

    # TODO: This should be handled by a Marshmallow schema and not created on the fly
    result = dict(
        dataset_name=dataset_name,
        dataset_permaname=dataset_permaname,
        dataset_version=str(dataset_version_version),
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        datafile_name=datafile_name,
        status=conversion_status,
        state=dataset_version.state.value,
        reason_state=dataset_version.reason_state,
        datafile_type=datafile.type,
        datafile_format=real_datafile.format.value,
        datafile_encoding=real_datafile.encoding,
    )

    if urls is not None:
        result["urls"] = urls

    if datafile.type == "virtual":
        result["underlying_file_id"] = datafile.underlying_file_id

    if result:
        models_controller.log_datafile_read_access_info(datafile.id)

    return result


@validate
def get_datafile(
    format,
    dataset_permaname=None,
    version=None,
    dataset_version_id=None,
    datafile_name=None,
    force=None,
):

    datafile = models_controller.find_datafile(
        dataset_permaname, version, dataset_version_id, datafile_name
    )

    if datafile is None:
        flask.abort(404)

    dataset_version = datafile.dataset_version
    dataset_version_version = dataset_version.version
    dataset_version_id = dataset_version.id
    dataset_id = dataset_version.dataset.id
    datafile_name = datafile.name
    dataset_name = dataset_version.dataset.name
    dataset_permaname = dataset_version.dataset.permaname
    dl_filename = _make_dl_name(
        datafile_name, dataset_version_version, dataset_name, format
    )

    if datafile.type == "virtual":
        real_datafile = datafile.underlying_data_file
    else:
        real_datafile = datafile

    if real_datafile.type == "gcs":
        real_datafile: GCSObjectDataFile
        result = _get_gcs_datafile(
            real_datafile,
            datafile,
            dataset_version,
            dataset_version_version,
            dataset_version_id,
            dataset_id,
            datafile_name,
            dataset_name,
            dataset_permaname,
            format,
        )
    else:
        real_datafile: S3DataFile
        result = _get_s3_datafile(
            real_datafile,
            datafile,
            dataset_version,
            dataset_version_version,
            dataset_version_id,
            dataset_id,
            datafile_name,
            dataset_name,
            dataset_permaname,
            dl_filename,
            force,
            format,
        )

    return flask.jsonify(result)


@validate
def get_datafile_short_summary(
    dataset_permaname=None, version=None, dataset_version_id=None, datafile_name=None
):
    datafile = models_controller.find_datafile(
        dataset_permaname, version, dataset_version_id, datafile_name
    )

    if datafile:
        return flask.jsonify(datafile.short_summary)
    else:
        flask.abort(404)


@validate
def get_datafile_column_types(
    dataset_permaname=None, version=None, dataset_version_id=None, datafile_name=None
):
    datafile = models_controller.find_datafile(
        dataset_permaname, version, dataset_version_id, datafile_name
    )
    if datafile is None:
        flask.abort(404)

    if datafile.type == "virtual":
        real_datafile = datafile.underlying_data_file
    else:
        real_datafile = datafile

    if real_datafile.type == "gcs":
        flask.abort(400)

    if real_datafile.format.name != "Columnar":
        flask.abort(400)

    real_datafile: S3DataFile
    return flask.jsonify(real_datafile.column_types_as_json)


@validate
def backfill_compressed_file(datafileId: str):
    if not models_controller.user_in_admin_group():
        flask.abort(403)

    return _backfill_compressed_file(datafileId)


def _backfill_compressed_file(datafile_id: str, delay=True):
    datafile = models_controller.get_datafile(datafile_id)
    if datafile.type != "s3" or datafile.compressed_s3_key is not None:
        return flask.make_response(flask.jsonify(None), 304)

    from taiga2.tasks import (
        convert_and_backfill_compressed_file,
        backfill_compressed_file,
    )

    if datafile.format == S3DataFile.DataFileFormat.Raw:
        task = backfill_compressed_file.delay(datafile_id, None)
    else:
        is_new, entry = models_controller.get_conversion_cache_entry(
            datafile.dataset_version.id, datafile.name, "csv"
        )

        if is_new:
            task = convert_and_backfill_compressed_file.delay(datafile_id, entry.id)
        else:
            task = backfill_compressed_file.delay(datafile_id, entry.id)

    return flask.make_response(flask.jsonify(task.id), 202)


@validate
def copy_datafile_to_google_bucket(datafileGCSCopy):
    # NOTE: This currently only works with datafiles that are s3 (or virtual s3) files
    # that have a compressed_s3_key (i.e. files that were created after the
    # introduction of compressed_s3_key or files that have been backfilled).

    datafile_id = datafileGCSCopy["datafile_id"]
    gcs_path = datafileGCSCopy["gcs_path"]

    datafile = models_controller.get_datafile_by_taiga_id(datafile_id)
    if datafile is None:
        raise flask.abort(404)

    if datafile.type == "virtual":
        datafile = datafile.underlying_data_file

    if datafile.type == "gcs":
        api_error("Cannot copy GCS pointer files")

    if datafile.compressed_s3_key is None:
        # TODO: backfill?
        api_error("Copying datafiles is only available for new files.")

    try:
        dest_bucket, dest_gcs_path = parse_gcs_path(gcs_path)
    except ValueError as e:
        api_error(str(e))

    # kick off task to download and upload
    from taiga2.tasks import (
        copy_datafile_to_google_bucket as _copy_datafile_to_google_bucket,
    )

    task = _copy_datafile_to_google_bucket.delay(
        datafile.id, dest_bucket, dest_gcs_path
    )

    return flask.jsonify(task.id)


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
    return task.state == "PENDING"


@validate
def move_to_trash(entryIds):
    print("Just received the entries to throw into the bin: {}".format(entryIds))
    models_controller.move_to_trash(entryIds)

    return flask.jsonify({})


@validate
def move_to_folder(moveMetadata):
    print("In move_to_folder, received {}".format(moveMetadata))
    entry_ids = moveMetadata["entryIds"]
    current_folder_id = moveMetadata["currentFolderId"]
    target_folder_id = moveMetadata.get("targetFolderId", None)
    print(
        "Just received the entries {} to move to the folder id {}, from the folder id {}".format(
            entry_ids, target_folder_id, current_folder_id
        )
    )

    return_data = {}

    try:
        models_controller.move_to_folder(
            entry_ids=entry_ids,
            current_folder_id=current_folder_id,
            target_folder_id=target_folder_id,
        )
    except NoResultFound:
        # TODO: Return an object with Success/Failure code + message to display
        return flask.abort(422)

    return flask.jsonify(return_data)


@validate
def copy_to_folder(copyMetadata):
    entry_ids = copyMetadata["entryIds"]
    folder_id = copyMetadata["folderId"]

    return_data = {}

    try:
        models_controller.copy_to_folder(
            entry_ids=entry_ids, target_folder_id=folder_id
        )
    except NoResultFound:
        # TODO: Return an object with Success/Failure code + message to display
        return flask.abort(422)

    return flask.jsonify(return_data)


@validate
def get_activity_log_for_dataset_id(datasetId):
    array_activity_log = models_controller.get_activity_for_dataset_id(datasetId)

    activity_log_schema = schemas.ActivityLogSchema(many=True)
    json_data_access_logs_entry = activity_log_schema.dump(array_activity_log).data

    return flask.jsonify(json_data_access_logs_entry)


def get_provenance_graph(gid):
    print("We received the graph Id: {}!".format(gid))
    provenance_full_graph_schema = schemas.ProvenanceGraphFullSchema()

    graph = models_controller.get_provenance_graph_by_id(gid)

    json_graph_data = provenance_full_graph_schema.dump(graph).data
    # We also need the url, so we add this to the json
    for provenance_node in json_graph_data["provenance_nodes"]:
        try:
            datafile = models_controller.get_datafile(provenance_node["datafile_id"])
            provenance_node["url"] = datafile.dataset_version_id
        except NoResultFound:
            log.info(
                "The node {} with datafile_id {} has been ignored because no datafile was matching".format(
                    provenance_node["node_id"], provenance_node["datafile_id"]
                )
            )

    return flask.jsonify(json_graph_data)


def import_provenance(provenanceData):
    """Import in the database a provenance Graph
    Input:
        - provenanceData => {name: string, graph: {nodes: [{label, type, id, (datafile_id)}],
            edges: [{from_id, to_id}]}
    """
    graph_name = provenanceData["name"]
    graph_nodes = provenanceData["graph"]["nodes"]
    graph_edges = provenanceData["graph"]["edges"]

    # TODO: Move this logic in models_controller
    new_graph = models_controller.add_graph(graph_permaname=None, graph_name=graph_name)

    for node in graph_nodes:
        # TODO: Manage existing node (same id)
        label = node["label"]
        node_type = node["type"]
        node_id = node.get("id")
        datafile_id = node.get("datafile_id", None)

        models_controller.add_node(
            graph_id=new_graph.graph_id,
            label=label,
            type=node_type,
            node_id=node_id,
            datafile_id=datafile_id,
        )

    for edge in graph_edges:
        label = edge.get("label", None)
        from_node_id = edge["from_id"]
        to_node_id = edge["to_id"]
        edge_id = edge.get("edge_id")

        models_controller.add_edge(
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            label=label,
            edge_id=edge_id,
        )

    return flask.jsonify(new_graph.graph_id)


def get_dataset_version_id_by_user_entry(entry_submitted_by_user: str):
    # TODO: Sanity check?
    dataset_version_id = models_controller.get_dataset_version_id_from_any(
        entry_submitted_by_user
    )

    if not dataset_version_id:
        flask.abort(404, "No entry found matching this submission")

    return flask.jsonify(dataset_version_id)


# Search
@validate
def search_within_folder(current_folder_id, search_query):
    """Given a folder id and a search query (string), will return all the datasets and folders that are matching the query inside the folder

    Example of json output:
    {
        'current_folder': {
            "name": folder.name,
            "id": folder.id
        },
        'name': "Search results for " + search_query + " within " + folder.name,
        'entries': [
            {
                "type": "folder",
                "id": "de0fbbfe942f4734b9aa3bf0e31f5595",
                "name": "Test_admin",
                "creation_date": "06/06/2017",
                "creator": {
                    "name": "rmarenco",
                    "id": "f54bc68c8619403eab4a6a0e768c9721"
                },
                "breadcrumbs": [
                    {
                        "order": 1,
                        "name": "Public",
                        "id": "public"
                    }
                ]
            },
            {
                "type": "dataset_version",
                "id": "6f16a4a01a89487e9f6f7b7a9913df58",
                "name": "Dataset admin",
                "creation_date": "06/06/2017",
                "creator": {
                    "name": "rmarenco",
                    "id": "f54bc68c8619403eab4a6a0e768c9721"
                },
                "breadcrumbs": [
                    {
                        "order": 1,
                        "name": "Public",
                        "id": "public"
                    },
                    {
                        "order": 2,
                        "name": "Test_admin",
                        "id": "de0fbbfe942f4734b9aa3bf0e31f5595"
                    }
                ]
            }
        ]
    }
    """
    # Get the folder
    folder = models_controller.get_folder(current_folder_id, one_or_none=True)
    if folder is None:
        flask.abort(404)

    # Search inside the folder
    breadcrumbs = []
    all_matching_entries = models_controller.find_matching_name(
        root_folder=folder, breadcrumbs=breadcrumbs, search_query=search_query
    )

    # TODO: Should also encapsulate this search to return a SearchResult we ask Marshmallow to jsonify
    search_name = "Search results for " + search_query + " within " + folder.name
    search_result = SearchResult(
        current_folder=folder, name=search_name, entries=all_matching_entries
    )

    # Jsonify through Marshmallow
    search_result_schema = schemas.SearchResultSchema()
    result = search_result_schema.dump(search_result).data

    return_response = {
        "current_folder": {"name": folder.name, "id": folder.id},
        "name": "Search results for " + search_query + " within " + folder.name,
        # 'entries': all_matching_entries
        "entries": [],
    }

    return flask.jsonify(result)


@validate
def get_all_groups_for_current_user():
    groups = models_controller.get_all_groups_for_current_user()
    group_list_schema = schemas.GroupSchema(many=True, exclude=["users"])
    result = group_list_schema.dump(groups).data
    return flask.jsonify(result)


@validate
def get_group(groupId):
    group = models_controller.get_group(groupId)
    if group is None:
        return flask.abort(404)
    if not models_controller.can_view_group(group.id):
        return flask.abort(403)

    group_schema = schemas.GroupSchema()
    result = group_schema.dump(group).data
    return flask.jsonify(result)


@validate
def add_group_user_associations(groupId, groupUserAssociationMetadata):
    user_ids = groupUserAssociationMetadata["userIds"]
    try:
        group = models_controller.add_group_user_associations(groupId, user_ids)
        if not group:
            return flask.abort(404)
        group_schema = schemas.GroupSchema()
        result = group_schema.dump(group).data
        return flask.jsonify(result)
    except AssertionError:
        return flask.abort(403)


@validate
def remove_group_user_associations(groupId, groupUserAssociationMetadata):
    user_ids = groupUserAssociationMetadata["userIds"]
    try:
        group = models_controller.remove_group_user_associations(groupId, user_ids)
        if not group:
            return flask.abort(404)
        group_schema = schemas.GroupSchema()
        result = group_schema.dump(group).data
        return flask.jsonify(result)
    except AssertionError:
        return flask.abort(403)


@validate
def add_figshare_token(token: str):
    if not figshare.is_token_valid(token):
        flask.abort(401)

    is_new = models_controller.add_figshare_token(token)
    if is_new:
        return flask.make_response(flask.jsonify({}), 201)
    else:
        return flask.jsonify({})


def _fetch_figshare_token() -> str:
    """Validates and returns token for current user.

    Also removes invalid tokens.
    """
    token = models_controller.get_figshare_personal_token_for_current_user()
    if token is None:
        return None

    if not figshare.is_token_valid(token):
        models_controller.remove_figshare_token_for_current_user()
        return None

    return token


def get_figshare_article_creation_options():
    categories = figshare.get_public_categories()
    licenses = figshare.get_public_licenses()
    return flask.jsonify({"categories": categories, "licenses": licenses})


@validate
def upload_dataset_version_to_figshare(figshareDatasetVersionLink):
    dataset_version_id = figshareDatasetVersionLink["dataset_version_id"]
    article_name = figshareDatasetVersionLink["article_name"]
    article_description = figshareDatasetVersionLink["article_description"]
    article_license = figshareDatasetVersionLink.get("license", 0)
    article_categories = figshareDatasetVersionLink.get("categories", None)
    article_keywords = figshareDatasetVersionLink.get("keywords", None)
    article_references = figshareDatasetVersionLink.get("references", None)

    files_to_upload = figshareDatasetVersionLink["files_to_upload"]

    token = figshare.fetch_figshare_token()
    if token is None:
        flask.abort(401)

    dataset_version = models_controller.get_dataset_version(dataset_version_id)
    figshare_dataset_version_link = figshare.create_article(
        dataset_version_id,
        article_name,
        article_description,
        article_license,
        article_categories,
        article_keywords,
        article_references,
        token,
    )

    from taiga2.tasks import upload_datafile_to_figshare

    for file_to_upload in files_to_upload:
        datafile = models_controller.get_datafile(file_to_upload["datafile_id"])
        if datafile.type == "gcs":
            file_to_upload["failure_reason"] = "Cannot upload GCS pointer files"
            continue
        elif datafile.type == "virtual":
            datafile = datafile.underlying_data_file

        if datafile.compressed_s3_key is None:
            file_to_upload[
                "failure_reason"
            ] = "Cannot upload files without compressed S3 file"
            continue

        task = upload_datafile_to_figshare.delay(
            figshare_dataset_version_link.figshare_article_id,
            figshare_dataset_version_link.id,
            file_to_upload["file_name"],
            file_to_upload["datafile_id"],
            datafile.compressed_s3_key,
            datafile.original_file_md5,
            token,
        )

        file_to_upload["task_id"] = task.id

    return flask.jsonify(
        {
            "article_id": figshare_dataset_version_link.figshare_article_id,
            "files": files_to_upload,
        }
    )


@validate
def update_figshare_article_with_dataset_version(figshareDatasetVersionLink):
    dataset_version_id = figshareDatasetVersionLink["dataset_version_id"]
    description = figshareDatasetVersionLink["description"]
    article_id = figshareDatasetVersionLink["article_id"]
    current_article_version = figshareDatasetVersionLink["current_article_version"]
    files_to_update = figshareDatasetVersionLink["files_to_update"]

    token = figshare.fetch_figshare_token()
    if token is None:
        flask.abort(401)

    dataset_version = models_controller.get_dataset_version(dataset_version_id)
    figshare_dataset_version_link = models_controller.add_figshare_dataset_version_link(
        dataset_version.id, article_id, current_article_version + 1
    )

    from taiga2.tasks import upload_datafile_to_figshare

    try:
        for file_to_update in files_to_update:
            action = file_to_update["action"]

            if action == "Delete":
                figshare.delete_file(
                    article_id, file_to_update["figshare_file_id"], token
                )
            elif action == "Add":
                datafile_id = file_to_update["datafile_id"]
                if datafile_id is None:
                    file_to_update[
                        "failure_reason"
                    ] = "Cannot add or replace file without datafile ID"
                    continue

                datafile = models_controller.get_datafile(datafile_id)

                if datafile.type == "gcs":
                    file_to_update["failure_reason"] = "Cannot upload GCS pointer files"
                    continue
                elif datafile.type == "virtual":
                    datafile = datafile.underlying_data_file

                if datafile.compressed_s3_key is None:
                    file_to_update[
                        "failure_reason"
                    ] = "Cannot upload files without compressed S3 file"
                    continue

                task = upload_datafile_to_figshare.delay(
                    figshare_dataset_version_link.figshare_article_id,
                    figshare_dataset_version_link.id,
                    file_to_update["file_name"],
                    datafile_id,
                    datafile.compressed_s3_key,
                    datafile.original_file_md5,
                    token,
                )

                file_to_update["task_id"] = task.id
            else:
                raise ValueError(f"Unrecognized action: {action}")

        r = figshare.update_article(article_id, description, token)

        return flask.jsonify(
            {
                "article_id": figshare_dataset_version_link.figshare_article_id,
                "files": files_to_update,
            }
        )
    except HTTPError as error:
        models_controller.delete_figshare_dataset_version_and_datafiles(
            figshare_dataset_version_link.id
        )
        return flask.abort(error.code, error.reason)


def get_public_article_information_for_user(article_id: int):
    try:
        article_info = figshare.get_public_article_information(article_id)
        token = figshare.fetch_figshare_token()
        if token is None:
            flask.abort(404)
        if not any(
            figshare.get_author(author["id"], token)
            for author in article_info["authors"]
        ):
            flask.abort(403)
        return flask.jsonify(article_info)
    except HTTPError as error:
        flask.abort(404)


def get_figshare_links_for_client(datasetVersionId: str):
    dataset_version = models_controller.get_dataset_version(datasetVersionId)
    if not dataset_version.figshare_dataset_version_link:
        flask.abort(404)

    try:
        article_files = figshare.get_public_article_files(
            dataset_version.figshare_dataset_version_link.figshare_article_id
        )

        figshare_file_ids_to_download_url = {
            f["id"]: f["download_url"] for f in article_files
        }
        figshare_datafile_links = models_controller.get_figshare_datafile_links_for_dataset_version_link(
            dataset_version.figshare_dataset_version_link.id
        )

        taiga_figshare_map = {
            "{}.{}/{}".format(
                dataset_version.dataset.permaname,
                dataset_version.version,
                l.datafile.name,
            ): {
                "download_url": figshare_file_ids_to_download_url[l.figshare_file_id],
                "format": l.datafile.format.value,
                "encoding": l.datafile.encoding
                if l.datafile.type == "s3"
                else l.datafile.underlying_data_file.encoding,
                "column_types": l.datafile.column_types_as_json
                if l.datafile.type == "s3"
                else l.datafile.underlying_data_file.column_types_as_json,
            }
            for l in figshare_datafile_links
        }

        buffer = BytesIO()
        buffer.write(json.dumps(taiga_figshare_map).encode())
        buffer.seek(0)
        return flask.jsonify({"content": json.dumps(taiga_figshare_map)})
    except HTTPError as error:
        flask.abort(404)


@validate
def add_dataset_subscription(dataset_id: str):
    """Subscribes the current user to dataset with id dataset_id"""
    subscription, is_new = models_controller.add_dataset_subscription(dataset_id)
    if is_new:
        return flask.make_response(flask.jsonify(subscription.id), 201)
    return flask.jsonify(subscription.id)


@validate
def delete_dataset_subscription(subscription_id: str):
    """Unsubscribes the current user to dataset with id dataset_id"""
    deleted = models_controller.delete_dataset_subscription(subscription_id)
    if deleted:
        return flask.jsonify(True)
    flask.abort(404)
