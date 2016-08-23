import json
from flask import current_app
import flask


def get_folder(folderId):
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

ADMIN_USER_ID = "admin"
def _get_user_id():
    return ADMIN_USER_ID

def get_user():
    user = current_app.db.get_user(_get_user_id())
    return flask.jsonify(user) 

def create_folder():
    pass

def update_folders():
    pass
def get_upload_url():
    pass

def create_dataset():
    pass

def get_dataset_activity():
    pass
def get_datafile():
    pass
def update_dataset_name():
    pass
def update_dataset_description():
    pass
def get_dataset_version():
    pass
def get_dataset_version_status():    
    pass
