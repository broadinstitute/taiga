from taiga2.api_app import create_app
from taiga2.celery_init import create_celery

# create the api_app to initialize the context that we use in celery tasks
_, api_app = create_app()

# create the celery app
app = create_celery(api_app)

