import connexion
import os
import logging

from taiga2.auth import init_backend_auth
from taiga2.conf import load_config
from taiga2.utils.exception_reporter import ExceptionReporter

log = logging.getLogger(__name__)

exception_reporter = ExceptionReporter()


def create_db():
    """Create the database, based on the app configuration,
    if it does not exist already"""
    from taiga2.models import db as _db

    _db.create_all()


def create_app(settings_override=None, settings_file=None):
    # create the flask app which handles api requests.  If settings_override is set, then settings
    # are overriden using the values in the provided dictionary.  Otherwise, the environment variable
    # TAIGA2_SETTINGS is used to look up a config file to use.

    from taiga2.models import db, migrate
    from taiga2.schemas import ma

    api_app = connexion.App(__name__, specification_dir="./swagger/")

    app = api_app.app

    load_config(app, settings_override=settings_override, settings_file=settings_file)

    api_app.add_api(
        "swagger.yaml",
        arguments={
            "title": "No descripton provided (generated by Swagger Codegen https://github.com/swagger-api/swagger-codegen)"
        },
    )

    # Init the database with the app
    db.init_app(app)

    # Init the migration with Alembic
    migrate.init_app(app, db)

    # Init the Serialization/Deserialization Schemas Marshmallow with the app
    # It needs to be done after the SQLAlchemy init
    ma.init_app(app)

    init_backend_auth(app)

    # Exception report with StackDriver
    exception_reporter.init_app(app=app, service_name="taiga-" + app.config["ENV"])
    register_errorhandlers(app=app)

    return api_app, app


def create_only_flask_app(settings_override=None, settings_file=None):
    api_app, app = create_app(
        settings_override=settings_override, settings_file=settings_file
    )
    return app


def register_errorhandlers(app):
    """Register error handlers."""

    def render_error(error):
        """Render error template."""
        # submit this exception to stackdriver if properly configured
        exception_reporter.report()
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, "code", 500)
        return error

    for errcode in [401, 403, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None
