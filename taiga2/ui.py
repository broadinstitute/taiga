import flask
from flask import Flask, render_template, send_from_directory, url_for
import os

app = Flask(__name__)


@app.route("/")
def index():
    return render_template('index.html', prefix=url_for('index'))


@app.route("/<path:filename>")
def sendindex2(filename):
    return render_template('index.html', prefix=url_for('index'))


@app.route("/js/<path:filename>")
def static_f(filename):
    return send_from_directory(os.path.abspath("node_modules"), filename)
