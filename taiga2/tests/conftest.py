import datetime
import os
import pytest

from flask import g

from taiga2.api_app import create_app
from taiga2.celery_init import configure_celery
from taiga2 import tasks

from taiga2.tests.monkeys import MonkeyS3

from taiga2.models import db as _db

import boto3

import os

# Temp db with different name for each test
dir_path = os.path.dirname(os.path.realpath(__file__))
TESTDB = os.path.join(dir_path, 'test_temp_taiga2.db')
TESTDB_PATH = "{}".format(TESTDB)
TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH


@pytest.fixture(scope='session')
def monkey_s3():
    s3 = MonkeyS3()
    return s3


@pytest.fixture(scope='session')
def app(request, monkey_s3):
    """Session-wide test `Flask` application."""
    settings_override = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URI,
        'SQLALCHEMY_TRACK_MODIFICATIONS': True,
        'SQLALCHEMY_ECHO': False,
        'BROKER_URL': None,
        'CELERY_RESULT_BACKEND': None,
        'CELERY_ALWAYS_EAGER': True
    }
    api_app, _app = create_app(settings_override)

    # create the celery app
    configure_celery(_app)

    # the celery worker uses this instance
    celery = tasks.celery

    print("Create app")

    # Establish an application context before running the tests.
    ctx = _app.app_context()
    ctx.push()

    # Monkey patch S3
    g._s3_client = monkey_s3

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

    # Return db and teardown
    yield _session
    transaction.rollback()
    connection.close()
    _session.remove()

#
# @pytest.fixture(scope='function')
# def s3(request):
#     _s3 = boto3.resource('s3')
#
#     yield _s3
#
#
# @pytest.fixture(scope='function')
# def bucket(s3, request):
#     # TODO: Not sure why I get an iterator there but not before
#     bucket_name = 'test_bucket'
#     s3.Bucket(bucket_name).create()
#     _bucket = s3.Bucket(bucket_name)
#
#     yield _bucket
#
#     _bucket.objects.delete()
#     _bucket.delete()




# @pytest.fixture(scope='session')
# def celery_config():
#     return {
#         'CELERY_BROKER_URL': 'redis://localhost:6379',
#         'CELERY_RESULT_BACKEND': 'redis://localhost:6379'
#     }

# @pytest.fixture(scope='session')
# def celery_parameters():
#     return {
#         'task_cls': 'redis://localhost:6379',
#         'CELERY_RESULT_BACKEND': 'redis://localhost:6379'
#     }


