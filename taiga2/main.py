from taiga2.api_app import create_app
from taiga2.ui import app as ui_app
from werkzeug.wsgi import pop_path_info, peek_path_info, DispatcherMiddleware, SharedDataMiddleware
from werkzeug.serving import run_simple
import configparser
import logging
import os
import sys
from taiga2.celery_init import configure_celery

log = logging.getLogger(__name__)


class PathDispatcher(object):
    "Delegate requests prefixed with 'api' to separate app"
    def __init__(self, api_app, frontend_app):
        self.api_app = api_app
        self.frontend_app = frontend_app

    def get_application(self, prefix):
        if prefix == "api":
            return self.api_app
        else:
            return self.frontend_app

    def __call__(self, environ, start_response):
        app = self.get_application(peek_path_info(environ))
        return app(environ, start_response)


def simple(env, resp):
    resp(b'200 OK', [(b'Content-Type', b'text/plain')])
    return [b"Hello WSGI World"]


def main():
    if len(sys.argv) != 2:
        log.error("Needs config file")
        sys.exit(-1)

    settings_file = sys.argv[1]

    api_app, flask_api_app = create_app(settings_file=settings_file)

    configure_celery(flask_api_app)

    debug = flask_api_app.config["DEBUG"]

    # application = PathDispatcher(api_app, ui_app)

    # shared_app = SharedDataMiddleware(simple, {
    # })
    prefix = flask_api_app.config["PREFIX"]
    prefix_with_api = os.path.join(prefix, 'api')
    parent_app = DispatcherMiddleware(simple, {
        prefix: ui_app,
        prefix_with_api: flask_api_app
    })

    # TODO: Should use the config file for the port and the ip address
    run_simple('0.0.0.0', 8080, parent_app,
               use_reloader=True, use_debugger=debug, use_evalex=True)
