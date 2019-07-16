from taiga2.celery_init import configure_celery
from taiga2 import tasks
from flask import current_app

configure_celery(current_app._get_current_object())
app = tasks.celery
