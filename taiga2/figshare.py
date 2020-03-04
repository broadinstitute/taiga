import boto3
import gzip
import hashlib
import io
import json
import os
import requests
import shutil
import tempfile
from requests.exceptions import HTTPError
from typing import Any, Dict, Optional, Tuple, Union
from typing_extensions import Literal, TypedDict

from flask import current_app

from taiga2.aws import aws

AUTH_URL = "https://figshare.com/account/applications/authorize{}"
BASE_URL = "https://api.figshare.com/v2/{}"
CHUNK_SIZE = 1024 * 1024


def raw_issue_request(method: str, url: str, token: str, data=None, binary=False):
    headers = {"Authorization": "token " + token}
    if data is not None and not binary:
        data = json.dumps(data)
    response = requests.request(method, url, headers=headers, data=data)
    try:
        response.raise_for_status()
        try:
            data = json.loads(response.content)
        except ValueError:
            data = response.content
    except HTTPError as error:
        raise error

    return data


def issue_request(method: str, endpoint: str, token: str, *args, **kwargs):
    return raw_issue_request(method, BASE_URL.format(endpoint), token, *args, **kwargs)


def validate_token(token: str, refresh_token: str) -> Tuple[str, str]:
    data = {
        "client_id": current_app.config["FIGSHARE_CLIENT_ID"],
        "client_secret": current_app.config["FIGSHARE_CLIENT_SECRET"],
        "grant_type": "authorization_code",
    }

    try:
        result = issue_request("GET", "token", token, data=data)
        return token, refresh_token
    except HTTPError as error:
        try:
            data["refresh_token"] = refresh_token
            result = issue_request("GET", "token", token, data=data)
            return result["token"], result["refresh_token"]
        except HTTPError as refresh_error:
            return None, None


def create_article(title: str, description: str, token: str):
    data = {"title": title, "description": description}
    result = issue_request("POST", "account/articles", token, data=data)

    result = raw_issue_request("GET", result["location"], token)

    return result["id"]


def get_file_check_data(download_dest, compressed_s3_key: str, md5: Optional[str]):
    s3 = aws.s3
    bucket_name = current_app.config["S3_BUCKET"]

    compressed_s3_object = s3.Object(bucket_name, compressed_s3_key)
    gzipped = io.BytesIO()

    compressed_s3_object.download_fileobj(gzipped)

    gzipped.seek(0)
    with gzip.GzipFile(fileobj=gzipped, mode="rb") as gz:
        shutil.copyfileobj(gz, download_dest)
        download_dest.seek(0)

        if md5 is None:
            md5_hash = hashlib.md5()
            data = download_dest.read(CHUNK_SIZE)
            while data:
                md5_hash.update(data)
                data = download_dest.read(CHUNK_SIZE)
            md5 = md5_hash.hexdigest()
        s = os.path.getsize(download_dest.name)
    return md5, s


def initiate_new_upload(
    article_id: int,
    file_name: str,
    compressed_s3_key: str,
    md5: Optional[str],
    token: str,
    download_dest,
) -> Dict[str, Any]:
    endpoint = "account/articles/{}/files".format(article_id)

    md5, size = get_file_check_data(download_dest, compressed_s3_key, None)

    data = {"name": file_name, "md5": md5, "size": size}

    result = issue_request("POST", endpoint, token, data=data)
    result = raw_issue_request("GET", result["location"], token)
    return result


def upload_parts(download_dest, file_info, token: str):
    url = "{upload_url}".format(**file_info)
    result = raw_issue_request("GET", url, token)

    for part in result["parts"]:
        upload_part(file_info, download_dest, part, token)


def upload_part(file_info, stream, part, token: str):
    udata = file_info.copy()
    udata.update(part)
    url = "{upload_url}/{partNo}".format(**udata)

    stream.seek(part["startOffset"])
    data = stream.read(part["endOffset"] - part["startOffset"] + 1)
    raw_issue_request("PUT", url, token, data=data, binary=True)


def complete_upload(article_id: int, file_id: str, token: str):
    issue_request(
        "POST", "account/articles/{}/files/{}".format(article_id, file_id), token
    )


def upload_datafile(
    new_article_id: int,
    file_name: str,
    compressed_s3_key: str,
    original_file_md5: Optional[str],
    token: str,
) -> Union[Tuple[Literal[True], int], Tuple[Literal[False], str]]:
    # Typing error: https://github.com/python/mypy/issues/7399
    with tempfile.NamedTemporaryFile("w+b") as download_dest:
        try:
            file_info = initiate_new_upload(
                new_article_id,
                file_name,
                compressed_s3_key,
                original_file_md5,
                token,
                download_dest,
            )
        except HTTPError as error:
            return False, str(error)

        try:
            upload_parts(download_dest, file_info, token)
        except HTTPError as error:
            return False, str(error)

        try:
            complete_upload(new_article_id, file_info["id"], token)
        except HTTPError as error:
            return False, str(error)

    return True, file_info["id"]
