import json
from flask import current_app
import flask

def datafile_get(name) -> str:
    return 'do some magic!'

def dataset_dataset_id_activity_get(datasetId) -> str:
    return 'do some magic!'

def dataset_dataset_id_description_post(datasetId) -> str:
    return 'do some magic!'

def dataset_dataset_id_name_post(datasetId) -> str:
    return 'do some magic!'

def dataset_version_dataset_version_id_get(datasetVersionId) -> str:
    return 'do some magic!'

def dataset_version_dataset_version_id_status_get(datasetVersionId) -> str:
    return 'do some magic!'

def dataset_version_dataset_version_id_update_post(datasetVersionId, modifications = None) -> str:
    return 'do some magic!'

def datasets_create_post(dataset = None) -> str:
    return 'do some magic!'

def folder_folder_id_get(folderId):
    db = current_app.db

    folder = db.get_folder(folderId)
    parents = [dict(name=f.name, id=f.id) for f in db.get_parent_folders(folderId)]
    entries = []
    for e in folder['entries']:
        if e.type == "folder":
            name = db.get_folder(e.id).name
        elif e.type == "dataset":
            name = db.get_dataset(e.id).name 
        elif e.type == "datasetVersion":
            name = db.get_dataset_version(e.id).name
        else:
            raise Exception("Unknown entry type: {}".format(e.type))

        entries.append(dict(id=e['id'], type=e['type'], name=name))

    response = dict(id = folder['id'],
        name=folder['name'],
        type=folder['type'],
        parents=parents,
        entries=entries)

    return flask.jsonify(response)

def folders_create_post(metadata = None) -> str:
    return 'do some magic!'

def folders_update_post(operations = None) -> str:
    return 'do some magic!'

def uploadurl_get() -> str:
    return 'do some magic!'

ADMIN_USER_ID = "admin"
def _get_user_id():
    return ADMIN_USER_ID

def user_get():
    user = current_app.db.get_user(_get_user_id())
    return flask.jsonify(dict(x="adfadf")) 

