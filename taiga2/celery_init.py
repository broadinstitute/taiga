from taiga2.tasks import celery


def configure_celery(app):
    celery.config_from_object(app.config)

    # only relevant for the worker process
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                print(app.config)
                return TaskBase.__call__(self, *args, **kwargs)

    if not app.config.get('CELERY_ALWAYS_EAGER', False):
        celery.Task = ContextTask

    return celery