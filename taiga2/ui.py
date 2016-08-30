from flask import Blueprint
from flask import Flask
import flask
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
    return flask.send_from_directory("node_modules", filename)

