import flask


def create_app(name, settings_override):
    print("We are in create_app factory")
    app = flask.Flask(name)

    for setting_key, setting_value in settings_override.items():
        app.config[setting_key] = setting_value

    # Init the database with the app
    from taiga2.models import db
    db.init_app(app)

    # Init the Serialization/Deserialization Schemas Marshmallow with the app
    # It needs to be done after the SQLAlchemy init
    from taiga2.schemas import ma
    ma.init_app(app)

    return app

