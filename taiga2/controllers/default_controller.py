import json
from flask import current_app
import flask
import time

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
        versions.append(dict(name=dv['version'], id=v, status="valid")) # =dv['status']))

    response = dict(id=ds['id'],
        name=ds['name'],
        description=ds['description'],
        permanames=ds['permanames'],
        versions=versions,
        acl=dict(default_permissions="owner", grants=[])
        )

    return flask.jsonify(response)
    
def get_folder(folderId):
    print("get_folder start", time.asctime())
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
        creation_date=folder['creation_date'],
        acl=dict(default_permissions="owner", grants=[])
        )
    print("get_folder stop", time.asctime())
    return flask.jsonify(response)

ADMIN_USER_ID = "admin"
def _get_user_id():
    return ADMIN_USER_ID

def get_user():
    print("get_user start", time.asctime())
    user = current_app.db.get_user(_get_user_id())
    print("get_user end", time.asctime())
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

    response = dict(id = dv['id'],
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
