from taiga2.api_app import exception_reporter
from taiga2.tasks import celery


def configure_celery(app):
    """Loads the configuration of CELERY from the Flask config and attaches celery to the app context.

    Returns the celery object"""
    celery.config_from_object(app.config)

    # only relevant for the worker process
    TaskBase = celery.Task

    class TaskWithStackdriverLogging(TaskBase):
        def on_failure(self, exc, task_id, args, kwargs, einfo):
            exception_reporter.report(with_request_context=False)
            super().on_failure(exc, task_id, args, kwargs, einfo)

    celery.Task = TaskWithStackdriverLogging

    return celery
