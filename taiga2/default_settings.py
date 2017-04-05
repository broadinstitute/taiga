# TODO: Move this into setting.cfg.sample so we can use the sample by default and it can stay iso with the required configuration

SQLALCHEMY_DATABASE_URI = 'sqlite:///taiga2.db'
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = True

# celery settings
BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND ='redis://localhost:6379'
S3_PREFIX = "upload/"
PREFIX="/taiga2"
# Frontend auth
# DEFAULT_USER_EMAIL = 'rmarenco@broadinstitute.org'

# S3 settings
CLIENT_UPLOAD_TOKEN_EXPIRY = 86400  # A day
