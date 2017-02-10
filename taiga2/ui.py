import flask
from flask import Flask, render_template, send_from_directory, url_for, request
import os

app = Flask(__name__)


def render_index_html():
    # TODO: If these headers are not populated, we should redirect the user to a not found or not authenticated page
    default_user_name = flask.current_app.config.get('TAKE_USER_NAME_FROM_HEADER', '')
    default_user_email = flask.current_app.config.get('TAKE_USER_EMAIL_FROM_HEADER', '')

    current_user_name = request.headers.get('X-Forwarded-User', default_user_name)
    current_user_email = request.headers.get('X-Forwarded-Email', default_user_email)
    return render_template('index.html',
                           prefix=url_for('index'),
                           current_user_name=current_user_name,
                           current_user_email=current_user_email)

@app.route("/")
def index():
    return render_index_html()


@app.route("/<path:filename>")
def sendindex2(filename):
    return render_index_html()


@app.route("/js/<path:filename>")
def static_f(filename):
    return send_from_directory(os.path.abspath("node_modules"), filename)
