import datetime
import os
import pytest

from flask import g
import flask

from taiga2.api_app import create_app
from taiga2.celery_init import configure_celery
from taiga2 import tasks

from taiga2.tests.monkeys import MonkeyS3, MonkeySTS

from taiga2.models import db as _db
from taiga2.controllers import models_controller as mc
import boto3

import os

# Temp db with different name for each test
dir_path = os.path.dirname(os.path.realpath(__file__))
TESTDB = os.path.join(dir_path, 'test_temp_taiga2.db')
TESTDB_PATH = "{}".format(TESTDB)
TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH


@pytest.fixture(scope='function')
def monkey_s3(tmpdir):
    s3 = MonkeyS3(str(tmpdir))
    return s3


@pytest.fixture(scope='function')
def monkey_sts():
    sts = MonkeySTS()
    return sts


@pytest.fixture(scope='function')
def app(request, monkey_s3, monkey_sts):
    """Session-wide test `Flask` application."""
    settings_override = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URI,
        'SQLALCHEMY_TRACK_MODIFICATIONS': True,
        'SQLALCHEMY_ECHO': False,
        'BROKER_URL': None,
        'CELERY_RESULT_BACKEND': None,
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
    g._s3_client = monkey_s3

    g._sts_client = monkey_sts

    # Return _app and teardown
    yield _app
    ctx.pop()


@pytest.fixture(scope='function')
def db(app, request):
    """Session-wide test database."""
    if os.path.exists(TESTDB_PATH):
        os.unlink(TESTDB_PATH)

    _db.create_all()

    # Return db and teardown
    yield _db
    _db.drop_all()
    os.unlink(TESTDB_PATH)


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
    u = mc.add_user("username",
                    "username@broadinstitute.org")
    return u.id

