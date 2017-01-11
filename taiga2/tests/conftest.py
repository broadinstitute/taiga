import os
import pytest

from taiga2.factory import create_app
from taiga2.models import db as _db
from flask_sqlalchemy import SQLAlchemy


TESTDB = 'test_taiga2.db'
TESTDB_PATH = "{}".format(TESTDB)
TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH


@pytest.fixture(scope='session')
def app(request):
    """Session-wide test `Flask` application."""
    settings_override = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URI,
        'SQLALCHEMY_TRACK_MODIFICATIONS': True,
        'SQLALCHEMY_ECHO': False
    }
    _app = create_app(__name__, settings_override)
    print("Create app")

    # Establish an application context before running the tests.
    ctx = _app.app_context()
    ctx.push()

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
