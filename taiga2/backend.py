import connexion
from celery import Celery


def create_app(name, settings_override):
    print("We are in create_app factory of {}".format(__name__))
    api_app = connexion.App(__name__, specification_dir='./swagger/')
    app = api_app.app

    for setting_key, setting_value in settings_override.items():
        app.config[setting_key] = setting_value

    # Init the database with the app
    from taiga2.models import db
    db.init_app(app)

    # Init the Serialization/Deserialization Schemas Marshmallow with the app
    # It needs to be done after the SQLAlchemy init
    from taiga2.schemas import ma
    ma.init_app(app)

    app.db_sqlAlchemy = db
    return api_app, app


settings_override = {
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///taiga2.db',
    'SQLALCHEMY_ECHO': True,
    'SQLALCHEMY_TRACK_MODIFICATIONS': True,
    'CELERY_BROKER_URL': 'redis://localhost:6379',
    'CELERY_RESULT_BACKEND': 'redis://localhost:6379'
    # 'CELERY_IMPORTS': ['taiga2.controllers.endpoint']
}

api_app, backend_app = create_app(__name__, settings_override)



