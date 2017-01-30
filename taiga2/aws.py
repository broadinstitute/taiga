import flask
import boto3
import logging
from flask import g

log = logging.getLogger(__name__)

class AWSClients:
    @property
    def s3(self):
        """
        Get a s3 client using the credentials in the config.

        To mock in a test, set flask.g._s3_client in test setup
        """
        config = flask.current_app.config
        if not hasattr(g, "_s3_client"):
            aws_access_key_id=config['AWS_ACCESS_KEY_ID']
            log.info("Getting S3 client with access key %s", aws_access_key_id)
            g._s3_client = boto3.resource('s3',
                                          aws_access_key_id=aws_access_key_id,
                                          aws_secret_access_key=config['AWS_SECRET_ACCESS_KEY'])
        return g._s3_client

    @property
    def client_upload_sts(self):
        """
        Get a STS client using credentials which are different the main credentials.  These credentials should
        only have access to perform object puts to the appropriate bucket.

        To mock in a test, set flask.g._client_upload_sts_client in test setup
        """
        config = flask.current_app.config
        if not hasattr(g, "_client_upload_sts_client"):
            aws_access_key_id=config['CLIENT_UPLOAD_AWS_ACCESS_KEY_ID']
            log.warn("Getting STS client with access key %s", aws_access_key_id)
            g._sts_client = boto3.client('sts',
                                         aws_access_key_id=aws_access_key_id,
                                         aws_secret_access_key=config['CLIENT_UPLOAD_AWS_SECRET_ACCESS_KEY'])
        return g._sts_client

aws = AWSClients()
