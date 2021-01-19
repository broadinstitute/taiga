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
from typing import Any, Dict, IO, List, Optional, Tuple, Union
from typing_extensions import Literal, TypedDict

from flask import current_app

import taiga2.controllers.models_controller as mc
from taiga2.third_party_clients.aws import aws
from taiga2.conv.util import Progress
from taiga2.models import DatasetVersion, FigshareDatasetVersionLink

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


def is_token_valid(token: str) -> bool:
    try:
        result = issue_request("GET", "account", token)
        return True
    except HTTPError as error:
        return False


FigshareCategory = TypedDict(
    "FigshareCategory", {"parent_id": int, "id": int, "title": str}
)


def get_public_categories() -> List[FigshareCategory]:
    r = issue_request("GET", "categories", "")
    return r


FigshareLicense = TypedDict("FigshareLicense", {"value": int, "name": str, "url": str})


def get_public_licenses() -> List[FigshareLicense]:
    r = issue_request("GET", "licenses", "")
    return r


def get_author(author_id: int, token: str):
    return issue_request("GET", "account/authors/{}".format(author_id), token)


def create_article(
    dataset_version_id: str,
    title: str,
    description: str,
    article_license: int,
    categories: List[int],
    keywords: List[str],
    references: List[str],
    token: str,
):
    data = {
        "title": title,
        "description": description,
        "defined_type": "dataset",
        "license": article_license,
    }
    if categories is not None and len(categories) > 0:
        data["categories"] = categories
    if keywords is not None and len(keywords) > 0:
        data["keywords"] = keywords
    if references is not None and len(references) > 0:
        data["references"] = references
    result = issue_request("POST", "account/articles", token, data=data)

    result = raw_issue_request("GET", result["location"], token)

    return mc.add_figshare_dataset_version_link(dataset_version_id, result["id"], 1)


def update_article(article_id: int, description: str, token: str):
    return issue_request(
        "PUT",
        "/account/articles/{}".format(article_id),
        token,
        data={"description": description},
    )


def get_file_check_data(download_dest: IO, compressed_s3_key: str, md5: Optional[str]):
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
    download_dest: IO,
) -> Dict[str, Any]:
    endpoint = "account/articles/{}/files".format(article_id)

    md5, size = get_file_check_data(download_dest, compressed_s3_key, None)

    data = {"name": file_name, "md5": md5, "size": size}

    result = issue_request("POST", endpoint, token, data=data)
    result = raw_issue_request("GET", result["location"], token)
    return result


def upload_parts(download_dest: IO, file_info, progress: Progress, token: str):
    url = "{upload_url}".format(**file_info)
    result = raw_issue_request("GET", url, token)

    num_parts = len(result["parts"])
    for i, part in enumerate(result["parts"]):
        upload_part(file_info, download_dest, part, token)
        progress.progress("Uploading to Figshare", current=float((i + 1) / num_parts))


def upload_part(file_info, download_dest: IO, part, token: str):
    udata = file_info.copy()
    udata.update(part)
    url = "{upload_url}/{partNo}".format(**udata)

    download_dest.seek(part["startOffset"])
    data = download_dest.read(part["endOffset"] - part["startOffset"] + 1)
    raw_issue_request("PUT", url, token, data=data, binary=True)


def complete_upload(article_id: int, file_id: str, token: str):
    issue_request(
        "POST", "account/articles/{}/files/{}".format(article_id, file_id), token
    )


def delete_file(article_id: int, file_id: int, token: str):
    return issue_request(
        "DELETE",
        "account/articles/{article_id}/files/{file_id}".format(
            article_id=article_id, file_id=file_id
        ),
        token,
    )


def get_public_article_information(
    article_id: int, article_version: Optional[int] = None
):
    if article_version is None:
        return issue_request("GET", "articles/{}".format(article_id), "")
    return issue_request(
        "GET", "articles/{}/versions/{}".format(article_id, article_version), ""
    )


def get_private_article_information(
    figshare_dataset_version_link: FigshareDatasetVersionLink,
):
    current_user = mc.get_current_session_user()
    if current_user.id == figshare_dataset_version_link.creator_id:
        token = mc.get_figshare_personal_token_for_current_user()
        if token is None:
            return None

        if not is_token_valid(token):
            mc.remove_figshare_token_for_current_user()
            return None

        return issue_request(
            "GET",
            "account/articles/{}".format(
                figshare_dataset_version_link.figshare_article_id
            ),
            token,
        )
    return None


def get_public_article_files(article_id: str):
    return issue_request("GET", "articles/{}/files".format(article_id), "")


def _update_article_information(figshare_article_info, dataset_version: DatasetVersion):
    figshare_article_info = {
        k: figshare_article_info[k]
        for k in (
            "description",
            "files",
            "id",
            "is_public",
            "status",
            "title",
            "url",
            "url_private_html",
            "url_public_html",
            "version",
        )
        if k in figshare_article_info
    }

    for i, file in enumerate(figshare_article_info["files"]):
        link = mc.get_figshare_datafile_link_by_figshare_id(file["id"])
        if link is not None:
            datafile = link.datafile
            if (
                datafile.dataset_version.dataset.id == dataset_version.dataset.id
                and datafile.dataset_version.version <= dataset_version.version
            ):
                figshare_article_info["files"][i]["taiga_datafile_id"] = datafile.id
                figshare_article_info["files"][i][
                    "taiga_datafile_readable_id"
                ] = "{}.{}/{}".format(
                    datafile.dataset_version.dataset.permaname,
                    datafile.dataset_version.version,
                    datafile.name,
                )
                if datafile.type == "virtual":
                    figshare_article_info["files"][i][
                        "underlying_file_id"
                    ] = datafile.underlying_file_id
                else:
                    figshare_article_info["files"][i][
                        "underlying_file_id"
                    ] = figshare_article_info["files"][i]["taiga_datafile_readable_id"]

    return figshare_article_info


def get_article_information(figshare_dataset_version_link: FigshareDatasetVersionLink):
    try:
        article_info = get_public_article_information(
            figshare_dataset_version_link.figshare_article_id,
            figshare_dataset_version_link.figshare_article_version,
        )
        return _update_article_information(
            article_info, figshare_dataset_version_link.dataset_version
        )

    except HTTPError as error:
        try:
            article_info = get_private_article_information(
                figshare_dataset_version_link
            )
            if article_info is None:
                raise error
            return _update_article_information(
                article_info, figshare_dataset_version_link.dataset_version
            )

        except HTTPError as error:
            return {"is_public": False}
