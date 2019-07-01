from taiga2.api_app import create_app
import logging
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


