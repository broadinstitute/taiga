import flask
import os

from taiga2.factory import create_app

settings_override = {
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///taiga2.db',
    'SQLALCHEMY_ECHO': True,
    'SQLALCHEMY_TRACK_MODIFICATIONS': True,

    # 'CELERY_IMPORTS': ['taiga2.controllers.endpoint']
}

# app = create_app(__name__, settings_override)
app = flask.Flask(__name__)

INDEX = "static/index.html"

@app.route("/")
def index():
    return flask.redirect("/app")

@app.route("/app")
def sendindex1():
    return flask.send_file(INDEX)

@app.route("/app/<path:filename>")
def sendindex2(filename):
    return flask.send_file(INDEX)

@app.route("/js/<path:filename>")
def static_f(filename):
    return flask.send_from_directory(os.path.abspath("node_modules"), filename)
