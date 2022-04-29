import flask
import logging
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

from taiga2.types import DatasetVersionMetadataDict, UploadVirtualDataFile

from .endpoint_validation import validate

from sqlalchemy.orm.exc import NoResultFound
from google.cloud import storage, exceptions as gcs_exceptions
from requests.exceptions import HTTPError

# TODO: Change the app containing db to api_app => current_app
from taiga2.models import (
    DatasetVersion,
)
from taiga2.third_party_clients.aws import (
    aws,
    create_signed_get_obj,
    create_s3_url as aws_create_s3_url,
)

from taiga2.third_party_clients.gcs import get_blob, parse_gcs_path

log = logging.getLogger(__name__)

# Handle URL upload
from flask import render_template, request, redirect, url_for
import os, json

from connexion.exceptions import ProblemException







