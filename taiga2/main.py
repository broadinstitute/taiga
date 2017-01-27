from taiga2.api_app import create_app
from taiga2.ui import app as ui_app
from werkzeug.wsgi import pop_path_info, peek_path_info
from werkzeug.serving import run_simple

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


def main():
    api_app, flask_api_app = create_app()
    debug = flask_api_app.config["DEBUG"]

    application = PathDispatcher(api_app, ui_app)

    run_simple('localhost', 8080, application,
               use_reloader=True, use_debugger=debug, use_evalex=True)
