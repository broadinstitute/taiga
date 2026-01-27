import hashlib
import logging
import flask
from flask import Flask, render_template, send_from_directory, url_for, current_app, abort
import os
import json
from taiga2.conf import load_config
from taiga2.auth import init_front_auth
from taiga2 import commands
from .extensions import db as ext_db, migrate
from taiga2 import models
from functools import lru_cache

log = logging.getLogger(__name__)


def register_extensions(app):
    # Init the database with the app
    ext_db.init_app(app)
    migrate.init_app(app, ext_db)


def register_commands(app):
    app.cli.add_command(commands.recreate_dev_db)
    app.cli.add_command(commands.run_worker)
    app.cli.add_command(commands.webpack)


def create_app(settings_override=None, settings_file=None):

    app = Flask(__name__)

    settings_file = os.environ.get("TAIGA_SETTINGS_FILE", settings_file)
    load_config(app, settings_file=settings_file, settings_override=settings_override)

    register_extensions(app)
    register_commands(app)

    # Add hooks for managing the authentication before each request
    init_front_auth(app)

    # Register the routes
    app.add_url_rule("/", view_func=index)
    app.add_url_rule("/<path:filename>", view_func=sendindex2)

    @app.context_processor
    def inject_webpack_url():
        return dict(webpack_url=webpack_url)

    return app


@lru_cache(maxsize=1)
def get_webpack_manifest():
    """Wepback outputs a manifest.json file which is a mapping from source
    filenames to output filenames. Each output filename contains a content hash
    which allows for cache busting."""
    try:
        filepath = os.path.join(current_app.static_folder, "webpack", "manifest.json")
        with open(file=filepath, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print("Webpack manifest.json not found. Did you forget to run webpack?")
        raise


def webpack_url(name):
    # If enabled, serve assets from webpack-dev-server.
    if current_app.config["USE_FRONTEND_DEV_SERVER"]:
        return "http://127.0.0.1:5001/webpack/" + name

    # Otherwise, look up the hashed filename and
    # serve from the Webpack output directory.
    manifest = get_webpack_manifest()
    return url_for('static', filename=f"webpack/{manifest[name]}")


def render_index_html():
    try:
        user_token = flask.g.current_user.token

        return render_template(
            "index.html", prefix=url_for("index"), user_token=user_token
        )
    except AttributeError:
        abort(403)


def index():
    return render_index_html()


def sendindex2(filename):
    return render_index_html()
