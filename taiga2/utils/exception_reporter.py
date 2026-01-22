from google.cloud import error_reporting
from flask import request
import flask


class ExceptionReporter:
    def __init__(self, service_name=None, app=None):
        self.service_name = service_name
        if app is not None:
            self.init_app(app)

    def init_app(self, app, service_name=None):
        if service_name is not None:
            self.service_name = service_name
        self.disabled = not app.config["REPORT_EXCEPTIONS"]
        # attempt to create a client, so we'll get an error on startup if there's a problem with credentials
        if not self.disabled:
            self._create_client()

    def report(self, with_request_context=True):
        if self.disabled:
            return

        client = self._get_client()
        if with_request_context:
            client.report_exception(
                http_context=error_reporting.build_flask_context(request)
            )
        else:
            client.report_exception()

    def _create_client(self):
        return error_reporting.Client(service=self.service_name, project="cds-logging")

    def _get_client(self):
        if not hasattr(flask.g, "stackdriver_client"):
            flask.g.stackdriver_client = self._create_client()
        return flask.g.stackdriver_client
