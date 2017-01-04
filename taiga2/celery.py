from celery import Celery

celery_app = Celery('taiga2',
                    broker='redis://localhost:6379',
                    backend='redis://localhost:6379',
                    include=[])

if __name__ == '__main__':
    celery_app.start()
