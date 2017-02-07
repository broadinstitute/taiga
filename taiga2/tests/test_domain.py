from flask_sqlalchemy import SessionBase

import taiga2.controllers.endpoint as endpoint

def test_endpoint_s3_credentials(app, session: SessionBase):
    dict_credentials = endpoint.get_s3_credentials()
    # TODO: Assert the dict content

