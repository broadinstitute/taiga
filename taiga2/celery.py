from taiga2.api_app import create_app
from taiga2.celery_init import configure_celery
from taiga2 import tasks
# create the api_app to initialize the context that we use in celery tasks
_, api_app = create_app()

# create the celery app
configure_celery(api_app)

# the celery worker uses this instance
celery = tasks.celery
