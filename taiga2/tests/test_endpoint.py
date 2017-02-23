import celery
import flask
import pytest

from flask_sqlalchemy import SessionBase

import taiga2.controllers.endpoint as endpoint
import taiga2.controllers.models_controller as models_controller
import taiga2.tasks as celery_tasks


def get_data_from_flask_jsonify(flask_jsonified):
    return flask.json.loads(flask_jsonified.data.decode('UTF8'))


def test_endpoint_s3_credentials(app, session: SessionBase):
    dict_credentials = endpoint.get_s3_credentials()
    # TODO: Assert the dict content


def test_create_new_upload_session(session: SessionBase):
    response_json_new_upload_session_id = endpoint.create_new_upload_session()
    new_upload_session_id = get_data_from_flask_jsonify(response_json_new_upload_session_id)
    assert models_controller.get_upload_session(new_upload_session_id) is not None


@pytest.fixture
def new_upload_session():
    response_json_new_upload_session_id = endpoint.create_new_upload_session()
    new_upload_session_id = get_data_from_flask_jsonify(response_json_new_upload_session_id)
    return models_controller.get_upload_session(new_upload_session_id)


def test_create_upload_session_file(app, session: SessionBase, new_upload_session):
    bucket = 'test_bucket'
    filetype = 'Raw'
    file_key = 'filekey'
    file_name = file_key

    S3UploadedFileMetadata = {
        'bucket': bucket,
        'filetype': filetype,
        'key': file_key,
        'filename': file_name
    }

    sid = new_upload_session.id

    response_json_create_upload_session_file = endpoint.create_upload_session_file(S3UploadedFileMetadata=S3UploadedFileMetadata,
                                                                                   sid=sid)
    task_id = get_data_from_flask_jsonify(response_json_create_upload_session_file)

    assert task_id is not None

    # Verify we have now a new upload session file in db
    _new_upload_session_files = models_controller.get_upload_session_files_from_session(sid)

    assert len(_new_upload_session_files) == 1
    assert _new_upload_session_files[0].filename == file_name


@pytest.fixture
def new_upload_session_file(session: SessionBase, new_upload_session):
    bucket = 'test_bucket'
    filetype = 'Raw'
    file_key = 'filekey'
    file_name = file_key

    S3UploadedFileMetadata = {
        'bucket': bucket,
        'filetype': filetype,
        'key': file_key,
        'filename': file_name
    }

    sid = new_upload_session.id

    endpoint.create_upload_session_file(S3UploadedFileMetadata=S3UploadedFileMetadata,
                                        sid=sid)
    _new_upload_session_files = models_controller.get_upload_session_files_from_session(sid)
    return _new_upload_session_files[0]


def test_create_dataset(session: SessionBase, new_upload_session_file):
    _new_upload_session_id = new_upload_session_file.session.id

    dataset_name = 'Dataset Name'
    dataset_description = 'Dataset Description'

    home_folder_id = models_controller.get_current_session_user().home_folder.id

    sessionDatasetInfo = {
        'sessionId': _new_upload_session_id,
        'datasetName': dataset_name,
        'datasetDescription': dataset_description,
        'currentFolderId': home_folder_id
    }
    response_json_create_dataset = endpoint.create_dataset(sessionDatasetInfo=sessionDatasetInfo)
    _new_dataset_id = get_data_from_flask_jsonify(response_json_create_dataset)

    assert _new_dataset_id is not None

    _new_dataset = models_controller.get_dataset(_new_dataset_id)

    assert _new_dataset.name == dataset_name
    assert _new_dataset.dataset_versions[0].datafiles[0].name == new_upload_session_file.filename


@pytest.fixture
def new_dataset(session: SessionBase, new_upload_session_file):
    _new_upload_session_id = new_upload_session_file.session.id

    dataset_name = 'Dataset Name'
    dataset_description = 'Dataset Description'

    home_folder_id = models_controller.get_current_session_user().home_folder.id

    sessionDatasetInfo = {
        'sessionId': _new_upload_session_id,
        'datasetName': dataset_name,
        'datasetDescription': dataset_description,
        'currentFolderId': home_folder_id
    }
    response_json_create_dataset = endpoint.create_dataset(sessionDatasetInfo=sessionDatasetInfo)
    _new_dataset_id = get_data_from_flask_jsonify(response_json_create_dataset)
    _new_dataset = models_controller.get_dataset(_new_dataset_id)
    return _new_dataset


def test_create_new_dataset_version(session: SessionBase, new_dataset, new_upload_session_file):
    session_id = new_upload_session_file.session.id

    # TODO: Get instead the last datasetVersion
    latest_dataset_version = new_dataset.dataset_versions[0]

    # We fetch the datafiles from the first dataset_version
    datafile_ids = [datafile.id
                    for datafile in latest_dataset_version.datafiles]

    datasetVersionMetadata = {
        'sessionId': session_id,
        'datasetId': new_dataset.id,
        'datafileIds': datafile_ids
    }

    response_json_create_new_dataset_version_id = endpoint.create_new_dataset_version(datasetVersionMetadata)
    new_dataset_version_id = get_data_from_flask_jsonify(response_json_create_new_dataset_version_id)

    _new_dataset_version = models_controller.get_dataset_version(new_dataset_version_id)

    assert _new_dataset_version.version == latest_dataset_version.version + 1
    # TODO: Test the number of uploaded files in the session + the number of datafile_ids instead
    assert len(_new_dataset_version.datafiles) == len(datafile_ids) + 1

    # TODO: Check if the datafiles in the new dataset_version are the same (filename/name) than in the new_upload_session_file + in the previous_dataset_version_datafiles
