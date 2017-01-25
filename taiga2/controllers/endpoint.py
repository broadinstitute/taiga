from flask import current_app, json
# TODO: Change the app containing db to api_app => current_app
import taiga2.controllers.models_controller as models_controller
import taiga2.schemas as schemas

# Handle URL upload
from flask import render_template, request, redirect, url_for
import os, json, boto3

from uuid import uuid4

import flask
import time


ADMIN_USER_ID = "admin"


def update_dataset():
    pass


# def get_dataset(datasetId):
#     db = current_app.db
#     ds = db.get_dataset(datasetId)
#     if ds is None:
#         flask.abort(404)
#
#     versions = []
#     for v in ds['versions']:
#         dv = db.get_dataset_version(v)
#         versions.append(dict(name=dv['version'], id=v, status="valid"))  # =dv['status']))
#
#     response = dict(id=ds['id'],
#                     name=ds['name'],
#                     description=ds['description'],
#                     permanames=ds['permanames'],
#                     versions=versions,
#                     acl=dict(default_permissions="owner", grants=[])
#                     )
#
#     return flask.jsonify(response)

def get_dataset(datasetId):
    dataset = models_controller.get_dataset(datasetId)
    if dataset is None:
        flask.abort(404)

    dataset_schema = schemas.DatasetSchema()
    json_dataset_data = dataset_schema.dump(dataset).data
    return flask.jsonify(json_dataset_data)


# def get_folder(folder_id):
#     print("get_folder start", time.asctime())
#     db = current_app.db
#
#     folder = db.get_folder(folder_id)
#     if folder is None:
#         flask.abort(404)
#
#     parents = [dict(name=f['name'], id=f['id']) for f in db.get_parent_folders(folder_id)]
#     entries = []
#     for e in folder['entries']:
#         if e['type'] == "folder":
#             f = db.get_folder(e['id'])
#             name = f['name']
#             creator_id = f['creator_id']
#             creation_date = f['creation_date']
#         elif e['type'] == "dataset":
#             d = db.get_dataset(e['id'])
#             name = d['name']
#             creator_id = d['creator_id']
#             creation_date = d['creation_date']
#         elif e['type'] == "dataset_version":
#             dv = db.get_dataset_version(e['id'])
#             print("dv=", dv)
#             d = db.get_dataset(dv['dataset_id'])
#             name = d['name']
#             creator_id = dv['creator_id']
#             creation_date = dv['creation_date']
#         else:
#             raise Exception("Unknown entry type: {}".format(e['type']))
#
#         creator = db.get_user(creator_id)
#         creator_name = creator['name']
#         entries.append(dict(
#             id=e['id'],
#             type=e['type'],
#             name=name,
#             creation_date=creation_date,
#             creator=dict(id=creator_id, name=creator_name)))
#
#     creator_id = folder['creator_id']
#     creator = db.get_user(creator_id)
#
#     response = dict(id=folder['id'],
#                     name=folder['name'],
#                     type=folder['type'],
#                     parents=parents,
#                     entries=entries,
#                     creator=dict(id=creator_id, name=creator['name']),
#                     creation_date=folder['creation_date'],
#                     acl=dict(default_permissions="owner", grants=[])
#                     )
#     print("get_folder stop", time.asctime())
#     return flask.jsonify(response)

    ## Used for Celery testing
    # response = tasks.get_folder_async.delay(folder_id)
    # return flask.jsonify(response.wait())


def get_folder(folder_id):
    print("get_folder start", time.asctime())
    folder = models_controller.get_folder(folder_id)
    if folder is None:
        flask.abort(404)

    folder_schema = schemas.FolderSchema()
    json_data_folder = folder_schema.dump(folder).data
    print("get_folder stop", time.asctime())
    return flask.jsonify(json_data_folder)


def _get_user_id():
    return ADMIN_USER_ID


# def get_user():
#     print("get_user start", time.asctime())
#     print("The user id called is: %s" % _get_user_id())
#     print("Can we get db_sqlAlchemy here? {}".format(current_app.db_sqlAlchemy))
#     db = current_app.db
#     user = db.get_user(_get_user_id())
#     print("user %s" % user)
#     print("get_user end", time.asctime())
#     return flask.jsonify(user)


def get_user():
    print("get_user start", time.asctime())
    user = models_controller.get_user(1)
    print("user %s" % user.name)
    print("get_user end", time.asctime())
    user_schema = schemas.UserSchema()
    json_data_user = user_schema.dump(user).data
    print("User jsonified: {}".format(json_data_user))
    return flask.jsonify(json_data_user)


def get_s3_credentials():
    """
    Create an access token to access S3 using the ~/.aws/credentials information
    :return: S3Credentials
    """
    # TODO: Use config instead of hard coding
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


def get_dataset_latest(dataset_id):
    latest_dataset_version = models_controller.get_latest_dataset_version(dataset_id)

    dataset_version_schema = schemas.DatasetVersionSummarySchema()
    json_data_latest_dataset_version = dataset_version_schema.dump(latest_dataset_version).data
    return flask.jsonify(json_data_latest_dataset_version)


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


# def get_dataset_version(datasetVersionId):
#     db = current_app.db
#     dv = db.get_dataset_version(datasetVersionId)
#     if dv is None:
#         flask.abort(404)
#
#     ds = db.get_dataset(dv['dataset_id'])
#
#     folder_objs = (db.get_folders_containing("dataset_version", datasetVersionId) +
#                    db.get_folders_containing("dataset", dv['dataset_id']))
#     folders = [dict(name=folder['name'], id=folder['id']) for folder in folder_objs]
#
#     datafiles = []
#     for e in dv['entries']:
#         datafiles.append(dict(
#             name=e['name'],
#             url=e['url'],
#             mime_type=e['type'],
#             description=e['description'],
#             content_summary=e["content_summary"]
#         ))
#
#     creator_id = dv['creator_id']
#     creator = db.get_user(creator_id)
#
#     response = dict(id=dv['id'],
#                     folders=folders,
#                     name=ds['name'],
#                     dataset_id=dv['dataset_id'],
#                     version=dv['version'],
#                     datafiles=datafiles,
#                     creator=dict(id=creator_id, name=creator['name']),
#                     creation_date=dv['creation_date'])
#
#     if 'provenance' in dv:
#         p = dv.get('provenance')
#         # add the dataset names to each source
#         for input in p["inputs"]:
#             dv_id = input["dataset_version_id"]
#             dv = db.get_dataset_version(dv_id)
#             ds = db.get_dataset(dv["dataset_id"])
#             name = "{} v{}".format(ds['name'], dv["version"])
#             input["dataset_version_name"] = name
#         response['provenance'] = p
#
#     return flask.jsonify(response)

def get_dataset_version(datasetVersion_id):
    dv = models_controller.get_dataset_version(dataset_version_id=int(datasetVersion_id))
    if dv is None:
        flask.abort(404)
    print("--- In  GET DATASET VERSION ----")
    print("--- DV {} ----".format(dv))
    print("--- DV PARENTS {} ----".format(dv.parents))
    for parent in dv.parents:
                         print("--- DV Parent id {} ----".format(parent.id))
                         print("--- DV Parent Name {} ----".format(parent.name))
    dataset_version_schema = schemas.DatasetVersionSchema()
    json_dv_data = dataset_version_schema.dump(dv).data
    print("--- JSON DV DATA {} ----".format(json_dv_data))
    return flask.jsonify(json_dv_data)


def get_dataset_version_status():
    pass


def process_new_datafile(S3UploadedFileMetadata, sid):

    # Launch a Celery process to convert and get back to populate the db + send finish to client
    # TODO: Do this in Celery instead
    # TODO: We should first check the file exists before adding it in the db
    # TODO: We could also check the type of the object
    # TODO: We need to make a distinction between numerical or table data
    # TODO: Add also Parquet file creation

    # Register this new file to the UploadSession received
    upload_session = models_controller.get_upload_session(sid)
    upload_session_file = models_controller.add_upload_session_file(sid, S3UploadedFileMetadata['key'])

    from taiga2.tasks import background_process_new_datafile
    result = background_process_new_datafile.delay(S3UploadedFileMetadata, sid, upload_session_file.id)
    # for i in range(20):
    #     print("In process_new_datafile, sleep and look the state of the task")
    #     status = taskstatus(result.id)
    #     print("TASKSTATUS {}".format(status))
    #     if status['state'] == 'SUCCESS':
    #         print('Received a success, we release this loop')
    #         break
    #     time.sleep(1)
    # # temp_hdf5_tcsv_file_path = result.get()
    # print("STOP for testing")
    return flask.jsonify(result.id)

    #     # Upload the HDF5 to s3 with the permaname as key
    #     with open(temp_hdf5_tcsv_file_path, 'rb') as data:
    #         object.upload_fileobj(data)
    #     print("Successfully uploaded the HDF5")
    #
    #     # Register the url into a datafile object
    #     # Store it in the db
    #     db_added_datafile = models_controller.add_datafile(name=datafile['key'],
    #                                                        permaname=permaname,
    #                                                        url=datafile['location'])
    #     # Add it to the first dataset
    #     # Add it to the user "Admin"
    #     # TODO: Replace by the current user
    #     admin = models_controller.get_user(1)
    #     # TODO: Get the dataset we would want to link it to
    #     db_added_dataset = models_controller.add_dataset(name=datafile['key'],
    #                                                      permaname=permaname,
    #                                                      creator_id=admin.id,
    #                                                      datafiles_ids=[db_added_datafile.id])
    #     folder_home_admin = admin.home_folder
    #     models_controller.add_folder_entry(folder_home_admin.id,
    #                                        db_added_dataset.id)
    #
    # return flask.jsonify({})


def get_new_upload_session():
    # TODO: Add the user_id related to this new session
    upload_session = models_controller.add_new_upload_session()
    return flask.jsonify(upload_session.id)


def task_status(taskStatusId):
    from taiga2.tasks import taskstatus
    status = taskstatus(taskStatusId)
    return flask.jsonify(status)