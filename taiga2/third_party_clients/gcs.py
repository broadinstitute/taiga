from datetime import timedelta
from typing import Optional, Tuple

from google.cloud import storage, exceptions as gcs_exceptions


def get_bucket(bucket_name: str) -> storage.Bucket:
    client = storage.Client()
    try:
        bucket = client.get_bucket(bucket_name)
    except gcs_exceptions.Forbidden as e:
        raise ValueError(
            "taiga-892@cds-logging.iam.gserviceaccount.com does not have storage.buckets.get access to bucket: {}".format(
                bucket_name
            )
        )
    except gcs_exceptions.NotFound as e:
        raise ValueError("No GCS bucket found: {}".format(bucket_name))
    return bucket


def create_signed_gcs_url(bucket_name, blob_name):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
    expiration_time = timedelta(minutes=1)

    url = blob.generate_signed_url(expiration=expiration_time, version="v4")
    return url


def upload_from_file(
    file_obj, dest_bucket: str, dest_path: str, content_type: str, content_encoding: str
):
    bucket = get_bucket(dest_bucket)
    blob = storage.Blob(dest_path, bucket)
    blob.content_type = content_type
    blob.content_encoding = content_encoding
    try:
        blob.upload_from_file(file_obj)
    except gcs_exceptions.Forbidden as e:
        raise ValueError(
            "taiga-892@cds-logging.iam.gserviceaccount.com does not have storage.buckets.create access to bucket: {}".format(
                dest_bucket
            )
        )

    return blob


def get_blob(bucket_name: str, object_name: str) -> Optional[storage.Blob]:
    bucket = get_bucket(bucket_name)
    blob = bucket.get_blob(object_name)

    return blob


def parse_gcs_path(gcs_path: str) -> Tuple[str, str]:
    # remove prefix
    if gcs_path.startswith("gs://"):
        gcs_path = gcs_path.replace("gs://", "")

    if "/" not in gcs_path:
        raise ValueError(
            "Invalid GCS path. '{}' is not in the form 'bucket_name/object_name'".format(
                gcs_path
            )
        )

    bucket_name, object_name = gcs_path.split("/", 1)
    return bucket_name, object_name
