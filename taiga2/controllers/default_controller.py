import json
from flask import current_app
import flask

def update_dataset():
    pass

def get_folder(folderId):
    db = current_app.db

    folder = db.get_folder(folderId)
    if folder is None:
        flask.abort(404)

    parents = [dict(name=f['name'], id=f['id']) for f in db.get_parent_folders(folderId)]
    entries = []
    for e in folder['entries']:
        if e['type'] == "folder":
            f = db.get_folder(e['id'])
            name = f['name']
            creator_id = f['creator_id']
            creation_date = f['creation_date']
        elif e['type'] == "dataset":
            d = db.get_dataset(e['id'])
            name = d['name']
            creator_id = d['creator_id']
            creation_date = d['creation_date']
        elif e['type'] == "dataset_version":
            dv = db.get_dataset_version(e['id'])
            print("dv=",dv)
            d = db.get_dataset(dv['dataset_id'])
            name = d['name']
            creator_id = dv['creator_id']
            creation_date = dv['creation_date']
        else:
            raise Exception("Unknown entry type: {}".format(e['type']))

        creator = db.get_user(creator_id)
        creator_name = creator['name']
        entries.append(dict(
            id=e['id'], 
            type=e['type'], 
            name=name,
            creation_date=creation_date,
            creator=dict(id=creator_id, name=creator_name)))

    creator_id = folder['creator_id']
    creator = db.get_user(creator_id)

    response = dict(id = folder['id'],
        name=folder['name'],
        type=folder['type'],
        parents=parents,
        entries=entries,
        creator=dict(id=creator_id, name=creator['name']),
        creation_date=folder['creation_date'])

    return flask.jsonify(response)

ADMIN_USER_ID = "admin"
def _get_user_id():
    return ADMIN_USER_ID

def get_user():
    user = current_app.db.get_user(_get_user_id())
    return flask.jsonify(user) 

def create_folder(metadata):
    db = current_app.db

    folder_id = db.add_folder(metadata['name'], 'folder', metadata['description'])
    db.add_folder_entry(metadata['parent'], folder_id, 'folder')

    return flask.jsonify(id=folder_id, name=metadata['name'])

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
def update_dataset_name():
    pass
def update_dataset_description():
    pass

def get_dataset_version(datasetVersionId):
    db = current_app.db

    dv = db.get_dataset_version(datasetVersionId)
    if folder is None:
        flask.abort(404)

    response = dict(id = dv['id'],
        name=d['name'],
        dataset_id=dv['dataset_id'],
        folders=folders,
        entries=entries,
        creator=dict(id=creator_id, name=creator['name']),
        creation_date=dv['creation_date'])

    return flask.jsonify(response)

def get_dataset_version_status():    
    pass
