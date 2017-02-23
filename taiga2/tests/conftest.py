import pytest

from flask import g
import flask

from taiga2.api_app import create_app
from taiga2.celery_init import configure_celery
from taiga2 import tasks

from taiga2.tests.mock_s3 import MockS3, MockSTS, MockS3Client

from taiga2.models import db as _db
from taiga2.controllers import models_controller as mc

import os
import logging

log = logging.getLogger(__name__)

TEST_USER_NAME = "username"
TEST_USER_EMAIL = "username@broadinstitute.org"
AUTH_HEADERS={'X-Forwarded-User': TEST_USER_NAME, 'X-Forwarded-Email': TEST_USER_EMAIL}


@pytest.fixture(scope='function')
def mock_s3(tmpdir):
    s3 = MockS3(str(tmpdir))
    return s3


@pytest.fixture(scope='function')
def mock_sts():
    sts = MockSTS()
    return sts


@pytest.fixture(scope='function')
def app(request, mock_s3, mock_sts):
    """Session-wide test `Flask` application."""
    settings_override = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'SQLALCHEMY_TRACK_MODIFICATIONS': True,
        'SQLALCHEMY_ECHO': False,
        'BROKER_URL': None,
        'CELERY_RESULT_BACKEND': None,
        # TODO: Change this. http://docs.celeryproject.org/en/latest/userguide/testing.html
        'CELERY_ALWAYS_EAGER': True,
        'S3_BUCKET': 'Test_Bucket'
    }
    api_app, _app = create_app(settings_override)

    # create the celery app
    configure_celery(_app)

    # the celery worker uses this instance
    celery = tasks.celery

    # Establish an application context before running the tests.
    ctx = _app.test_request_context()
    ctx.push()

    # Monkey patch S3
    g._s3_resource = mock_s3

    g._s3_client = MockS3Client()

    g._sts_client = mock_sts

    # Celery of the app
    g._celery_instance = celery

    # Return _app and teardown
    yield _app
    ctx.pop()


@pytest.fixture(scope='function')
def db(app, request):
    """Session-wide test database."""
    _db.create_all()

    # Return db and teardown
    yield _db


@pytest.fixture(scope='function')
def session(db, request):
    """Creates a new database session for a test."""
    print("Begin session")
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    _session = db.create_scoped_session(options=options)

    db.session = _session

    # We call before_request
    flask.current_app.preprocess_request()

    # Return db and teardown
    yield _session
    transaction.rollback()
    connection.close()
    _session.remove()


@pytest.fixture(scope="function")
def user_id(db):
    u = mc.add_user(TEST_USER_NAME,
                    TEST_USER_EMAIL)
    return u.id

