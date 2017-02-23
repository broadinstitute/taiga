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