SQLALCHEMY_DATABASE_URI = 'sqlite:///taiga2.db'
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = True

# celery settings
BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND ='redis://localhost:6379'


