from flask import Flask
import flask
app = Flask(__name__)

@app.route("/app")
def sendindex1():
    return flask.send_file("index.html")

@app.route("/app/<path:filename>")
def sendindex2(filename):
    return flask.send_file("index.html")

@app.route("/s/<path:filename>")
def static_fs(filename):
    return flask.send_from_directory(".", filename)

@app.route("/<path:filename>")
def static_f(filename):
    return flask.send_from_directory(".", filename)

if __name__ == "__main__":
    app.run(debug=True)