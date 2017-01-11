import flask


def create_app(name, settings_override):
    print("We are in create_app factory")
    app = flask.Flask(name)

    for setting_key, setting_value in settings_override.items():
        app.config[setting_key] = setting_value

    from taiga2.models import db
    db.init_app(app)

    return app

