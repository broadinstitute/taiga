import flask
import logging
import time

from sqlalchemy.orm.exc import NoResultFound

# TODO: Change the app containing db to api_app => current_app
import taiga2.controllers.models_controller as models_controller
import taiga2.schemas as schemas
import taiga2.conv as conversion
from taiga2.models import DataFile, normalize_name

from taiga2.aws import aws
from taiga2.aws import create_signed_get_obj
from taiga2.aws import create_s3_url as aws_create_s3_url

log = logging.getLogger(__name__)

# Handle URL upload
from flask import render_template, request, redirect, url_for
import os, json


ADMIN_USER_ID = "admin"


def get_dataset(datasetId):
    # try using ID
    dataset = models_controller.get_dataset(datasetId, one_or_none=True)

    # if that failed, try by permaname
    if dataset is None:
        dataset = models_controller.get_dataset_from_permaname(datasetId, one_or_none=True)

    if dataset is None:
        flask.abort(404)

    # TODO: We should instead check in the controller, but did not want to repeat
    # Remove folders that are not allowed to be seen
    allowed_dataset = dataset
    allowed_dataset.parents = filter_allowed_parents(dataset.parents)

    # Get the rights of the user over the folder
    right = models_controller.get_rights(dataset.id)

    dataset_schema = schemas.DatasetSchema()
    print("The right is: {}".format(right))
    dataset_schema.context['entry_user_right'] = right
    json_dataset_data = dataset_schema.dump(allowed_dataset).data
    return flask.jsonify(json_dataset_data)


def get_datasets(datasetIdsDict):
    array_dataset_ids = datasetIdsDict['datasetIds']

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


def create_folder(metadata):
    """Create a folder given a metadata dictionary of this form:
    metadata['name'], metadata['description'], metadata['parentId']"""
    # TODO: Add the add_folder_entry inside the add_folder function?
    folder_name = metadata['name']
    folder_description = metadata['description']
    parent_id = metadata['parentId']

    new_folder = models_controller.add_folder(name=folder_name,
                                              folder_type=models_controller.Folder.FolderType.folder,
                                              description=folder_description)
    models_controller.add_folder_entry(parent_id, new_folder.id)

    folder_named_id_schema = schemas.FolderNamedIdSchema()
    json_folder_named_id = folder_named_id_schema.dump(new_folder).data

    return flask.jsonify(json_folder_named_id)


def get_folder(folder_id):
    folder = models_controller.get_folder(folder_id, one_or_none=True)
    if folder is None:
        flask.abort(404)

    folder.parents = filter_allowed_parents(folder.parents)

    # Get the rights of the user over the folder
    right = models_controller.get_rights(folder_id)

    folder_schema = schemas.FolderSchema()
    folder_schema.context['entry_user_right'] = right
    json_data_folder = folder_schema.dump(folder).data

    return flask.jsonify(json_data_folder)


def update_folder_name(folderId, NameUpdate):
    updated_folder = models_controller.update_folder_name(folderId, NameUpdate["name"])

    return flask.jsonify({updated_folder.id})


def update_folder_description(folderId, DescriptionUpdate):
    updated_folder = models_controller.update_folder_description(folderId, DescriptionUpdate["description"])

    return flask.jsonify({updated_folder.id})


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

    right = models_controller.get_rights(first_dataset_version.id)

    dataset_version_schema = schemas.DatasetVersionSchema()
    dataset_version_schema.context['entry_user_right'] = right
    json_data_first_dataset_version = dataset_version_schema.dump(first_dataset_version).data
    return flask.jsonify(json_data_first_dataset_version)


def get_dataset_last(dataset_id):
    last_dataset_version = models_controller.get_latest_dataset_version(dataset_id)

    right = models_controller.get_rights(last_dataset_version.id)

    dataset_version_schema = schemas.DatasetVersionSchema()
    dataset_version_schema.context['entry_user_right'] = right
    json_data_first_dataset_version = dataset_version_schema.dump(last_dataset_version).data
    return flask.jsonify(json_data_first_dataset_version)


def update_dataset_name(datasetId, NameUpdate):
    updated_dataset = models_controller.update_dataset_name(datasetId, NameUpdate["name"])

    return flask.jsonify({updated_dataset.id})


def update_dataset_description(datasetId, DescriptionUpdate):
    updated_dataset = models_controller.update_dataset_description(datasetId, DescriptionUpdate["description"])

    return flask.jsonify({updated_dataset.id})


def create_or_update_dataset_access_log(datasetId):
    access_log = models_controller.add_or_update_dataset_access_log(datasetId)
    return flask.jsonify({access_log.id})


def get_datasets_access_logs():
    array_access_logs = models_controller.get_datasets_access_logs()

    access_log_schema = schemas.AccessLogSchema(many=True)
    json_data_access_logs_current_user_datasets = access_log_schema.dump(array_access_logs).data

    return flask.jsonify(json_data_access_logs_current_user_datasets)


def get_entry_access_logs(entryId):
    array_access_logs = models_controller.get_entry_access_logs(entryId)

    access_log_schema = schemas.AccessLogSchema(many=True)
    json_data_access_logs_entry = access_log_schema.dump(array_access_logs).data

    return flask.jsonify(json_data_access_logs_entry)


def get_entries_access_logs():
    array_access_logs = models_controller.get_entries_access_logs()

    access_log_schema = schemas.AccessLogSchema(many=True)
    json_data_access_logs_current_user_entries = access_log_schema.dump(array_access_logs).data

    return flask.jsonify(json_data_access_logs_current_user_entries)


def accessLogs_remove(accessLogsToRemove):
    models_controller.remove_accessLogs(accessLogsToRemove)
    return flask.jsonify({})


def create_or_update_entry_access_log(entryId):
    models_controller.add_or_update_entry_access_log(entryId)
    return flask.jsonify({})


def get_dataset_version(datasetVersion_id):
    dv = models_controller.get_dataset_version(dataset_version_id=datasetVersion_id, one_or_none=True)
    if dv is None:
        flask.abort(404)

    dataset_version_right = models_controller.get_rights(dv.id)

    dataset_version_schema = schemas.DatasetVersionSchema()
    dataset_version_schema.context['entry_user_right'] = dataset_version_right
    json_dv_data = dataset_version_schema.dump(dv).data

    return flask.jsonify(json_dv_data)


def get_dataset_versions(datasetVersionIdsDict):
    array_dataset_version_ids = datasetVersionIdsDict['datasetVersionIds']
    dataset_versions = models_controller.get_dataset_versions_bulk(array_dataset_version_ids)

    dataset_version_schema = schemas.DatasetVersionSchema(many=True)

    # TODO: IMPORTANT and bug potential => Manage here the missing context depending on the dataset_v
    dataset_version_schema.context['entry_user_right'] = models_controller.EntryRightsEnum.can_view

    json_data_dataset_versions = dataset_version_schema.dump(dataset_versions).data

    return flask.jsonify(json_data_dataset_versions)


def get_dataset_version_from_dataset(datasetId, datasetVersionId):
    dataset_version_schema = schemas.DatasetVersionSchema()
    dataset_schema = schemas.DatasetSchema()

    dataset_version = models_controller \
        .get_dataset_version_by_dataset_id_and_dataset_version_id(datasetId,
                                                                  datasetVersionId, one_or_none=True)
    if dataset_version is None:
        # if we couldn't find a version by dataset_version_id, try permaname and version number.
        version_number = None
        try:
            version_number = int(datasetVersionId)
        except ValueError:
            # TODO: Log the error
            pass

        if version_number is not None:
            dataset_version = models_controller.get_dataset_version_by_permaname_and_version(datasetId, version_number, one_or_none=True)
        else:
            dataset_version = models_controller.get_latest_dataset_version_by_permaname(datasetId)

    if dataset_version is None:
        flask.abort(404)

    dataset_version_right = models_controller.get_rights(dataset_version.id)

    dataset = dataset_version.dataset
    dataset_right = models_controller.get_rights(dataset.id)

    dataset.parents = filter_allowed_parents(dataset.parents)

    dataset_version_schema.context['entry_user_right'] = dataset_version_right
    json_dv_data = dataset_version_schema.dump(dataset_version).data

    dataset_schema.context['entry_user_right'] = dataset_right
    json_dataset_data = dataset_schema.dump(dataset).data

    # Preparation of the dictonary to return both objects
    json_dv_and_dataset_data = {'datasetVersion': json_dv_data, 'dataset': json_dataset_data}

    return flask.jsonify(json_dv_and_dataset_data)


def update_dataset_version_description(datasetVersionId, DescriptionUpdate):
    models_controller.update_dataset_version_description(datasetVersionId,
                                                         DescriptionUpdate["description"])
    return flask.jsonify({})


def create_upload_session_file(S3UploadedFileMetadata, sid):
    s3_bucket = S3UploadedFileMetadata['bucket']

    initial_file_type = S3UploadedFileMetadata['filetype']
    initial_s3_key = S3UploadedFileMetadata['key']
    filename = S3UploadedFileMetadata['filename']

    # Register this new file to the UploadSession received
    upload_session_file = models_controller.add_upload_session_file(session_id=sid,
                                                                    filename=filename,
                                                                    initial_file_type=initial_file_type,
                                                                    initial_s3_key=initial_s3_key,
                                                                    s3_bucket=s3_bucket)

    # Launch a Celery process to convert and get back to populate the db + send finish to client
    from taiga2.tasks import background_process_new_upload_session_file
    task = background_process_new_upload_session_file.delay(upload_session_file.id, initial_s3_key, initial_file_type,
                                                            s3_bucket, upload_session_file.converted_s3_key)

    return flask.jsonify(task.id)


def create_new_upload_session():
    upload_session = models_controller.add_new_upload_session()
    return flask.jsonify(upload_session.id)


def create_dataset(sessionDatasetInfo):
    session_id = sessionDatasetInfo['sessionId']
    dataset_name = sessionDatasetInfo['datasetName']
    dataset_description = sessionDatasetInfo.get('datasetDescription', None)
    current_folder_id = sessionDatasetInfo['currentFolderId']

    added_dataset = models_controller.add_dataset_from_session(session_id,
                                                               dataset_name,
                                                               dataset_description,
                                                               current_folder_id)

    return flask.jsonify(added_dataset.id)


def create_new_dataset_version(datasetVersionMetadata):
    session_id = datasetVersionMetadata['sessionId']
    dataset_id = datasetVersionMetadata['datasetId']
    new_description = datasetVersionMetadata['newDescription']
    existing_datafiles_id = datasetVersionMetadata['datafileIds']

    new_dataset_version = models_controller.create_new_dataset_version_from_session(session_id,
                                                                                    dataset_id,
                                                                                    existing_datafiles_id,
                                                                                    new_description=new_description)

    return flask.jsonify(new_dataset_version.id)


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


def _make_dl_name(datafile_name, dataset_version_version, dataset_name, format):
    if format != 'raw':
        suffix = '.'+format
    else:
        suffix = ""

    name = "{}_v{}-{}{}".format(normalize_name(dataset_name), dataset_version_version, normalize_name(datafile_name), suffix)
    return name


def get_datafile(format, dataset_permaname=None, version=None, dataset_version_id=None, datafile_name=None, force=None):
    from taiga2.tasks import start_conversion_task

    datafile = models_controller.find_datafile(dataset_permaname, version, dataset_version_id, datafile_name)

    if datafile is None:
        flask.abort(404)

    # import pdb; pdb.set_trace()
    dataset_version = datafile.dataset_version
    dataset_version_version = dataset_version.version
    dataset_version_id = dataset_version.id
    dataset_id = dataset_version.dataset.id
    datafile_name = datafile.name
    dataset_name = dataset_version.dataset.name
    dataset_permaname = dataset_version.dataset.permaname
    dl_filename = _make_dl_name(datafile_name, dataset_version_version, dataset_name, format)

    if format == "metadata":
        urls = None
        conversion_status = "Completed successfully"
    elif _no_transform_needed(format, datafile.type):
        # no conversion is necessary
        urls = [create_signed_get_obj(datafile.s3_bucket, datafile.s3_key, dl_filename)]
        conversion_status = "Completed successfully"
    else:
        force_conversion = force == "Y"
        is_new, entry = models_controller.get_conversion_cache_entry(dataset_version_id, datafile_name, format)

        from taiga2 import models
        if not is_new:
            if entry.state == models.ConversionEntryState.failed and not force_conversion:
                log.error("For entry {}, entry.state is failed and force_conversion is not set."
                          "Reporting internal error.".format(entry.id))
                flask.abort(500)  # report internal error
            elif not entry_is_valid(entry) or force_conversion:
                log.warning("Cache entry not associated with a running task, deleting to try again")
                models_controller.delete_conversion_cache_entry(entry.id)
                is_new, entry = models_controller.get_conversion_cache_entry(dataset_version_id, datafile_name, format)

        if is_new:
            t = start_conversion_task.delay(datafile.s3_bucket, datafile.s3_key, str(datafile.type), format, entry.id)
            models_controller.update_conversion_cache_entry_with_task_id(entry.id, t.id)

        urls = models_controller.get_signed_urls_from_cache_entry(entry.urls_as_json, dl_filename)
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


def get_datafile_short_summary(dataset_permaname=None,
                               version=None,
                               dataset_version_id=None,
                               datafile_name=None):
    datafile = models_controller.find_datafile(dataset_permaname, version, dataset_version_id, datafile_name)

    if datafile:
        return flask.jsonify(datafile.short_summary)
    else:
        flask.abort(404)


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


def move_to_folder(moveMetadata):
    print("In move_to_folder, received {}".format(moveMetadata))
    entry_ids = moveMetadata["entryIds"]
    current_folder_id = moveMetadata["currentFolderId"]
    target_folder_id = moveMetadata.get("targetFolderId", None)
    print("Just received the entries {} to move to the folder id {}, from the folder id {}" \
          .format(entry_ids, target_folder_id, current_folder_id))

    return_data = {}

    try:
        models_controller.move_to_folder(entry_ids=entry_ids,
                                         current_folder_id=current_folder_id,
                                         target_folder_id=target_folder_id)
    except NoResultFound:
        # TODO: Return an object with Success/Failure code + message to display
        return flask.abort(422)

    return flask.jsonify(return_data)


def copy_to_folder(copyMetadata):
    entry_ids = copyMetadata["entryIds"]
    folder_id = copyMetadata["folderId"]

    return_data = {}

    try:
        models_controller.copy_to_folder(entry_ids=entry_ids, target_folder_id=folder_id)
    except NoResultFound:
        # TODO: Return an object with Success/Failure code + message to display
        return flask.abort(422)

    return flask.jsonify(return_data)


def get_provenance_graph(gid):
    print("We received the graph Id: {}!".format(gid))
    provenance_full_graph_schema = schemas.ProvenanceGraphFullSchema()

    graph = models_controller.get_provenance_graph_by_id(gid)

    json_graph_data = provenance_full_graph_schema.dump(graph).data
    # We also need the url, so we add this to the json
    for provenance_node in json_graph_data['provenance_nodes']:
        try:
            datafile = models_controller.get_datafile(provenance_node['datafile_id'])
            provenance_node['url'] = datafile.dataset_version_id
        except NoResultFound:
            log.info("The node {} with datafile_id {} has been ignored because no datafile was matching"\
                     .format(provenance_node['node_id'], provenance_node['datafile_id']))

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
        label = node['label']
        node_type = node['type']
        node_id = node.get('id')
        datafile_id = node.get('datafile_id', None)

        models_controller.add_node(graph_id=new_graph.graph_id,
                                   label=label,
                                   type=node_type,
                                   node_id=node_id,
                                   datafile_id=datafile_id)

    for edge in graph_edges:
        label = edge.get('label', None)
        from_node_id = edge['from_id']
        to_node_id = edge['to_id']
        edge_id = edge.get('edge_id')

        models_controller.add_edge(from_node_id=from_node_id,
                                   to_node_id=to_node_id,
                                   label=label,
                                   edge_id=edge_id)

    return flask.jsonify(new_graph.graph_id)


def filter_allowed_parents(parents):
    allowed_parents = parents

    for index, folder in enumerate(parents):
        if not models_controller.can_view(folder.id):
            del allowed_parents[index]

    return allowed_parents
