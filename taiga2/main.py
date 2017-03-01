from taiga2.api_app import create_app
from taiga2.ui import create_app as ui_create_app
from werkzeug.wsgi import pop_path_info, peek_path_info, DispatcherMiddleware, SharedDataMiddleware
from werkzeug.serving import run_simple
import configparser
import logging
import os
import sys
from taiga2.celery_init import configure_celery, celery

log = logging.getLogger(__name__)


def run_celery_worker():
    if len(sys.argv) != 2:
        log.error("Needs config file")
        sys.exit(-1)

    settings_file = sys.argv[1]

    api_app, flask_api_app = create_app(settings_file=settings_file)

    configure_celery(flask_api_app)
    celery.worker_main(['', '-B'])


def main():
    if len(sys.argv) != 2:
        log.error("Needs config file")
        sys.exit(-1)

    settings_file = sys.argv[1]

    # Init Api/Backend app
    api_app, flask_api_app = create_app(settings_file=settings_file)

    configure_celery(flask_api_app)

    debug = flask_api_app.config["DEBUG"]

    # Init frontend app
    # ui_create_app uses also default_settings.py
    ui_app = ui_create_app(settings_file=settings_file)

    prefix = flask_api_app.config["PREFIX"]
    assert prefix.startswith("/")
    prefix_with_api = os.path.join(prefix, 'api')

    def _unhandled_url(env, resp):
        resp(b'200 OK', [(b'Content-Type', b'text/plain')])
        return ["This url has no handler.  Instead, try going to {}".format(prefix).encode("utf8")]

    parent_app = DispatcherMiddleware(_unhandled_url, {
        prefix: ui_app,
        prefix_with_api: flask_api_app
    })

    # TODO: Should use the config file for the port and the ip address
    run_simple('0.0.0.0', 8080, parent_app,
               use_reloader=True, use_debugger=debug, use_evalex=True,
               threaded=True)
