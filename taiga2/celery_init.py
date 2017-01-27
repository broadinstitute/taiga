from celery import Celery

def create_celery(app):
    celery = Celery("taiga2", include=['taiga2.tasks'])
    celery.config_from_object(app.config)

    # only relevant for the worker process
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask

    return celery