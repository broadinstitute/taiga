import hashlib
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
    app.add_url_rule('/pseudostatic/<hash>/<path:filename>', view_func=pseudostatic)
    app.add_url_rule('/<path:filename>', view_func=sendindex2)
    app.add_url_rule('/js/<path:filename>', view_func=static_f)

    @app.context_processor
    def inject_pseudostatic_url():
        return dict(pseudostatic_url=pseudostatic_url)

    return app


PSEUDOSTATIC_CACHE = {}
def pseudostatic_url(name):
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
    abs_filename = os.path.abspath(os.path.join(static_dir, name))
    assert abs_filename.startswith(static_dir)

    hash = None
    if name in PSEUDOSTATIC_CACHE:
        hash, mtime = PSEUDOSTATIC_CACHE[abs_filename]
        if mtime != os.path.getmtime(abs_filename):
            hash = None

    if hash is None:
        mtime = os.path.getmtime(abs_filename)
        hash_md5 = hashlib.md5()
        with open(abs_filename, "rb") as fd:
            for chunk in iter(lambda: fd.read(40960), b""):
                hash_md5.update(chunk)
        hash = hash_md5.hexdigest()
        PSEUDOSTATIC_CACHE[abs_filename] = (hash, mtime)
        log.debug("Caching hash of %s as %s", abs_filename, hash)

    return flask.url_for("pseudostatic", hash=hash, filename=name)


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


def pseudostatic(hash, filename):
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    return flask.send_from_directory(static_dir, filename)