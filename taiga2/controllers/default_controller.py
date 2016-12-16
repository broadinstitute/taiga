from flask import current_app
# Handle URL upload
from flask import render_template, request, redirect, url_for
import os, json, boto3

from uuid import uuid4

import flask
import time

from .. import tasks

ADMIN_USER_ID = "admin"


def update_dataset():
    pass


def get_dataset(datasetId):
    db = current_app.db
    ds = db.get_dataset(datasetId)
    if ds is None:
        flask.abort(404)

    versions = []
    for v in ds['versions']:
        dv = db.get_dataset_version(v)
        versions.append(dict(name=dv['version'], id=v, status="valid"))  # =dv['status']))

    response = dict(id=ds['id'],
                    name=ds['name'],
                    description=ds['description'],
                    permanames=ds['permanames'],
                    versions=versions,
                    acl=dict(default_permissions="owner", grants=[])
                    )

    return flask.jsonify(response)


def get_folder(folder_id):
    print("get_folder start", time.asctime())
    response = tasks.get_folder_async.delay(folder_id)
    return flask.jsonify(response.wait())


def _get_user_id():
    return ADMIN_USER_ID


def get_user():
    print("get_user start", time.asctime())
    print("The user id called is: %s" % _get_user_id())
    db = current_app.db
    user = db.get_user(_get_user_id())
    print("user %s" % user)
    print("get_user end", time.asctime())
    return flask.jsonify(user)


def get_s3_credentials():
    """
    Create an access token to a specific bucket in S3 using the ~/.aws/credentials information
    :return: S3Credentials
    """
    # TODO: Use config instead of hard coding
    s3_bucket = 'broadtaiga2prototype'
    key = uuid4().hex
    expires_in = 900

    sts = boto3.client('sts')

    temporary_session_credentials = sts.get_session_token(
        DurationSeconds=expires_in
    )

    print("We just generated this temp session credentials:")

    dict_credentials = temporary_session_credentials['Credentials']

    model_frontend_credentials = {
        'accessKeyId': dict_credentials['AccessKeyId'],
        'expiration': dict_credentials['Expiration'],
        'secretAccessKey': dict_credentials['SecretAccessKey'],
        'sessionToken': dict_credentials['SessionToken']
    }

    # See frontend/models/models.ts for the S3Credentials object
    return flask.jsonify(model_frontend_credentials)


def create_folder(metadata):
    db = current_app.db
    # TODO: Add the add_folder_entry inside the add_folder function?
    folder_id = db.add_folder(metadata['name'], 'folder', metadata['description'])
    db.add_folder_entry(metadata['parent'], folder_id, 'folder')

    return flask.jsonify(id=folder_id, name=metadata['name'])


def create_dataset(metadata):
    db = current_app.db
    dataset_version_id = db.create_dataset(_get_user_id(), metadata['name'], metadata['description'], )


def update_folders(operations):
    pass


def get_upload_url():
    pass


def create_dataset():
    pass


def get_dataset_activity():
    pass


def get_datafile():
    pass


def update_dataset_name(datasetId, NameUpdate):
    print("dataset_id", datasetId)
    print("new_name", NameUpdate)

    db = current_app.db
    db.update_dataset_name(_get_user_id(), datasetId, NameUpdate["name"])
    return flask.jsonify({})


def update_dataset_description(datasetId, DescriptionUpdate):
    print("dataset_id", datasetId)
    print("new_name", DescriptionUpdate)

    db = current_app.db
    db.update_dataset_description(_get_user_id(), datasetId, DescriptionUpdate["description"])
    return flask.jsonify({})


def get_dataset_version(datasetVersionId):
    db = current_app.db
    dv = db.get_dataset_version(datasetVersionId)
    if dv is None:
        flask.abort(404)

    ds = db.get_dataset(dv['dataset_id'])

    folder_objs = (db.get_folders_containing("dataset_version", datasetVersionId) +
                   db.get_folders_containing("dataset", dv['dataset_id']))
    folders = [dict(name=folder['name'], id=folder['id']) for folder in folder_objs]

    datafiles = []
    for e in dv['entries']:
        datafiles.append(dict(
            name=e['name'],
            url=e['url'],
            mime_type=e['type'],
            description=e['description'],
            content_summary=e["content_summary"]
        ))

    creator_id = dv['creator_id']
    creator = db.get_user(creator_id)

    response = dict(id=dv['id'],
                    folders=folders,
                    name=ds['name'],
                    dataset_id=dv['dataset_id'],
                    version=dv['version'],
                    datafiles=datafiles,
                    creator=dict(id=creator_id, name=creator['name']),
                    creation_date=dv['creation_date'])

    if 'provenance' in dv:
        p = dv.get('provenance')
        # add the dataset names to each source
        for input in p["inputs"]:
            dv_id = input["dataset_version_id"]
            dv = db.get_dataset_version(dv_id)
            ds = db.get_dataset(dv["dataset_id"])
            name = "{} v{}".format(ds['name'], dv["version"])
            input["dataset_version_name"] = name
        response['provenance'] = p

    return flask.jsonify(response)


def get_dataset_version_status():
    pass
