import logging
import flask
from flask import Flask, render_template, send_from_directory, url_for, request
import os
from taiga2.conf import load_config
from taiga2.auth import init_front_auth

log = logging.getLogger(__name__)

def create_app(settings_override=None, settings_file=None):
    from taiga2.models import db

    app = Flask(__name__)

    load_config(app, settings_file=settings_file, settings_override=settings_override)

    # Init the database with the app
    db.init_app(app)

    # Add hooks for managing the authentication before each request
    init_front_auth(app)

    # Register the routes
    app.add_url_rule('/', view_func=index)
    app.add_url_rule('/<path:filename>', view_func=sendindex2)
    app.add_url_rule('/js/<path:filename>', view_func=static_f)

    return app


def render_index_html():
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
