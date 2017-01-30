import connexion
import os
import logging

log = logging.getLogger(__name__)

def create_db():
    """Create the database, based on the app configuration,
    if it does not exist already"""
    from taiga2.models import db as _db
    _db.create_all()
    print(_db)

def create_app(settings_override=None, settings_file=None):
    # create the flask app which handles api requests.  If settings_override is set, then settings
    # are overriden using the values in the provided dictionary.  Otherwise, the environment variable
    # TAIGA2_SETTINGS is used to look up a config file to use.

    from taiga2.models import db
    from taiga2.schemas import ma

    print("We are in create_app factory of {}".format(__name__))
    api_app = connexion.App(__name__, specification_dir='./swagger/')
    api_app.add_api('swagger.yaml',
                    arguments={
                        'title': 'No descripton provided (generated by Swagger Codegen https://github.com/swagger-api/swagger-codegen)'})
    app = api_app.app
    app.config.from_object('taiga2.default_settings')
    if settings_override is not None:
        app.config.update(settings_override)
    elif settings_file is not None:
        if os.path.exists(settings_file):
            settings_file = os.path.abspath(settings_file)
            log.warn("Loading settings from %s", settings_file)
            app.config.from_pyfile(settings_file)
    else:
        if "TAIGA2_SETTINGS" in os.environ:
            settings_file = os.path.abspath(os.environ['TAIGA2_SETTINGS'])
            log.warn("Loading settings from (envvar TAIGA2_SETTINGS): %s", settings_file)
            app.config.from_pyfile(settings_file)

    # Init the database with the app
    db.init_app(app)

    # Init the Serialization/Deserialization Schemas Marshmallow with the app
    # It needs to be done after the SQLAlchemy init
    ma.init_app(app)

    return api_app, app





