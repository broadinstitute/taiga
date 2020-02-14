import hashlib
import json
import os
import requests

from requests.exceptions import HTTPError

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


def list_articles(token: str):
    result = issue_request("GET", "account/articles", token)
    print("Listing current articles:")
    if result:
        for item in result:
            print(u"  {url} - {title}".format(**item))
    else:
        print("  No articles.")
    print()


def create_article(title: str, token: str):
    data = {
        "title": title  # You may add any other information about the article here as you wish.
    }
    result = issue_request("POST", "account/articles", token, data=data)
    print("Created article:", result["location"], "\n")

    result = raw_issue_request("GET", result["location"], token)

    return result["id"]


def list_files_of_article(article_id: str, token: str):
    result = issue_request("GET", "account/articles/{}/files".format(article_id), token)
    print("Listing files for article {}:".format(article_id))
    if result:
        for item in result:
            print("  {id} - {name}".format(**item))
    else:
        print("  No files.")

    print()


def get_file_check_data(file_name: str):
    with open(file_name, "rb") as fin:
        md5 = hashlib.md5()
        size = 0
        data = fin.read(CHUNK_SIZE)
        while data:
            size += len(data)
            md5.update(data)
            data = fin.read(CHUNK_SIZE)
        return md5.hexdigest(), size


def initiate_new_upload(article_id: str, file_name: str, token: str):
    endpoint = "account/articles/{}/files"
    endpoint = endpoint.format(article_id)

    md5, size = get_file_check_data(file_name)
    data = {"name": os.path.basename(file_name), "md5": md5, "size": size}

    result = issue_request("POST", endpoint, token, data=data)
    print("Initiated file upload:", result["location"], "\n")

    result = raw_issue_request("GET", result["location"], token)

    return result


def complete_upload(article_id: str, file_id: str, token: str):
    issue_request(
        "POST", "account/articles/{}/files/{}".format(article_id, file_id), token
    )


def upload_parts(file_path, file_info, token: str):
    url = "{upload_url}".format(**file_info)
    result = raw_issue_request("GET", url, token)

    print("Uploading parts:")
    with open(file_path, "rb") as fin:
        for part in result["parts"]:
            upload_part(file_info, fin, part, token)
    print()


def upload_part(file_info, stream, part, token: str):
    udata = file_info.copy()
    udata.update(part)
    url = "{upload_url}/{partNo}".format(**udata)

    stream.seek(part["startOffset"])
    data = stream.read(part["endOffset"] - part["startOffset"] + 1)

    raw_issue_request("PUT", url, token, data=data, binary=True)
    print("  Uploaded part {partNo} from {startOffset} to {endOffset}".format(**part))
