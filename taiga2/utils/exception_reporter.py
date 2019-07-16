from google.cloud import error_reporting
from flask import request

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


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

    def report(self):
        if self.disabled:
            return

        client = self._get_client()
        client.report_exception(
            http_context=error_reporting.build_flask_context(request)
        )

    def _create_client(self):
        return error_reporting.Client(service=self.service_name, project="cds-logging")

    def _get_client(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, "stackdriver_client"):
                ctx.stackdriver_client = self._create_client()
            return ctx.stackdriver_client
        raise Exception("Missing context")
