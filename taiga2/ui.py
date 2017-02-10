import logging
import flask
from flask import Flask, render_template, send_from_directory, url_for, request
import os

from taiga2.auth import init_front_auth

log = logging.getLogger(__name__)


def create_app(settings_override=None, settings_file=None):
    from taiga2.models import db
    from taiga2.schemas import ma

    app = Flask(__name__)

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

    # Add hooks for managing the authentication before each request
    init_front_auth(app)

    # Register the routes
    app.add_url_rule('/', view_func=index)
    app.add_url_rule('/<path:filename>', view_func=sendindex2)
    app.add_url_rule('/js/<path:filename>', view_func=static_f)

    return app


def render_index_html():
    # TODO: If these headers are not populated, we should redirect the user to a not found or not authenticated page
    # default_user_name = flask.current_app.config.get('TAKE_USER_NAME_FROM_HEADER', '')
    # default_user_email = flask.current_app.config.get('TAKE_USER_EMAIL_FROM_HEADER', '')

    # current_user_name = request.headers.get('X-Forwarded-User', default_user_name)
    # current_user_email = request.headers.get('X-Forwarded-Email', default_user_email)
    user_token = flask.g.current_user.token
    return render_template('index.html',
                           prefix=url_for('index'),
                           user_token=user_token)


def index():
    return render_index_html()


def sendindex2(filename):
    return render_index_html()


def static_f(filename):
    return send_from_directory(os.path.abspath("node_modules"), filename)
