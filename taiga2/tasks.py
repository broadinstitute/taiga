import time

from . import persist
from .celery import celery_app



@celery_app.task
def get_folder_async(folder_id):
    """Celery task to fetch the folder from the Database"""
    print("We are in Celery!")

    db = persist.open_db('test.json')
    print("Testing db: %s" % db.get_user('admin'))

    folder = db.get_folder(folder_id)
    if folder is None:
        # TODO: replace flask.abort(404) by an error flag that we will catch in the caller
        # flask.abort(404)
        print("We did not find the folder_id %s" % folder_id)
        return None

    parents = [dict(name=f['name'], id=f['id']) for f in db.get_parent_folders(folder_id)]
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
            print("dv=", dv)
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

    response = dict(id=folder['id'],
                    name=folder['name'],
                    type=folder['type'],
                    parents=parents,
                    entries=entries,
                    creator=dict(id=creator_id, name=creator['name']),
                    creation_date=folder['creation_date'],
                    acl=dict(default_permissions="owner", grants=[])
                    )
    print("get_folder stop", time.asctime())
    return response
