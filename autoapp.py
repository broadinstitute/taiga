# -*- coding: utf-8 -*-
"""Create an application instance."""
import os

from taiga2.api_app import create_app
from taiga2.ui import create_app as ui_create_app
from taiga2.celery_init import configure_celery, celery

from werkzeug.wsgi import DispatcherMiddleware

settings_file = os.getenv("TAIGASETTINGSFILE", "settings.cfg")

print("Using settings from: {}".format(settings_file))

# Init Api/Backend app
api_app, flask_api_app = create_app(settings_file=settings_file)
configure_celery(flask_api_app)
debug = flask_api_app.config["DEBUG"]

# Init frontend app
# ui_create_app uses also default_settings.py
app = ui_create_app(settings_file=settings_file)

prefix = flask_api_app.config["PREFIX"]
assert prefix.startswith("/")
prefix_with_api = os.path.join(prefix, 'api')

def _no_content_response(env, resp):
    resp(b'200 OK', [(b'Content-Type', b'text/plain')])
    return ["This url has no handler.  Instead, try going to {}".format(prefix).encode("utf8")]

app.wsgi_app = DispatcherMiddleware(_no_content_response, {
    prefix: app.wsgi_app,
    prefix_with_api: flask_api_app.wsgi_app
})


