import os
import uuid
import collections

from tinydb import TinyDB, Query

DatasetFile = collections.namedtuple("DatasetFile", "name description type datafile_id")

def new_id():
    return uuid.uuid4().hex

class Db:
    def __init__(self, db):
        self.db = db
        self.users = db.table("users")
        self.folders = db.table("folders")
        self.datafiles = db.table("datafiles")
        self.datasets = db.table("datasets")
        self.datasetVersions = db.table("datasetVersions")
        self.activity = db.table("activity")

    def add_user(self, name, home_folder_id, trash_folder_id):
        id = new_id()
        self.users.insert(
            dict(id=id,
                name=name,
                home_folder_id=home_folder_id,
                trash_folder_id=trash_folder_id
            ))
        return id
    
    def get_user(self, user_id):
        User = Query()
        return self.users.get(User.id == user_id)

    def update_folder_name(self, folder_id, name):
        Folder = Query()
        self.folders.update(dict(name=name), Folder.id == folder_id)        

    def update_folder_description(self, folder_id, name):
        Folder = Query()
        self.folders.update(dict(description=description), Folder.id == folder_id)        

    def add_folder(self, name, type, description):
        assert type in ['home', 'trash', 'folder']

        id = new_id()
        self.folders.insert(
            dict(id=id,
                name=name,
                type=type,
                description=description,
                entries=[]))
        return id

    def get_folder(self, id):
        Folder = Query()
        return self.folders.get(Folder.id == id)

    def add_folder_entry(self, folder_id, id, type):
        def add_entry(f):
            for entry in f['entries']:
                if entry['id'] == id and entry['type'] == type:
                    return f
            f['entries'].append(dict(id=id, type=type))
            return f

        Folder = Query()
        self.folders.update(add_entry, Folder.id == folder_id)

    def remove_folder_entry(self, folder_id, id, type):
        def remove_entry(f):
            f['entries'] = [entry for entry in f['entries'] if entry['id'] != id or entry['type'] != type]
            return f

        Folder = Query()
        self.folders.update(remove_entry, Folder.id == folder_id)
    
    def get_parent_folders(self, folder_id):
        def is_parent(entries):
            for e in entries:
                if e['type'] == "folder" and e['id'] == folder_id:
                    return True
            return False
        Folder = Query()
        parent_folders = self.folders.search(Folder.entries.test(is_parent))
        return parent_folders

    def register_datafile_id(self, id, url):
        self.datafiles.insert(dict(id=id, url=url))

    def _convert_entries_to_dict(self, entries):
        def get_url_for(datafile_id):
            Datafile = Query()
            df = self.datafiles.get(Datafile.id == datafile_id)
            return df['url']

        d_entries = [ dict(
            name=e.name,
            description=e.description,
            url=get_url_for(e.datafile_id)
        ) for e in entries]

        return d_entries

    def create_dataset(self, user_id, name, description, entries):
        dataset_id = new_id()
        dataset_version_id = new_id()

        d_entries = self._convert_entries_to_dict(entries)

        self.datasets.insert(dict(
            id=dataset_id,
            name=name,
            description=description,
            versions=[dataset_version_id]
            ))

        self.datasetVersions.insert(dict(
            id=dataset_version_id,
            dataset_id=dataset_id,
            entries=d_entries
            ))

        self.activity.insert(dict(user_id=user_id, dataset_id=dataset_id, message="Created"))

        return dataset_version_id

    def update_dataset_name(self, user_id, dataset_id, name):
        Dataset = Query()
        self.datasets.update(dict(name=name), Dataset.id == dataset_id)        
        self.activity.insert(dict(user_id=user_id, dataset_id=dataset_id, message="Changed name"))

    def update_dataset_description(self, user_id, dataset_id, description):
        Dataset = Query()
        self.datasets.update(dict(description=description), Dataset.id == dataset_id)        
        self.activity.insert(dict(user_id=user_id, dataset_id=dataset_id, message="Changed description"))

    def update_dataset_contents(self, user_id, dataset_id, entries_to_remove, entries_to_add, comments):
        Dataset = Query()
        dataset = self.datasets.get(Dataset.id == dataset_id)

        last_version_id = dataset['versions'][-1]

        DatasetVersion = Query()
        prev_dataset_version = self.datasetVersions(DatasetVersion.id == last_version_id)

        new_entries = [e for e in prev_dataset_version['entries'] if e[name] not in entries_to_remove]
        d_entries = self._convert_entries_to_dict(entries_to_add)
        new_entries.extend(d_entries)

        dataset_version_id = new_id()
        self.datasetVersions.insert(dict(
            id=dataset_version_id,
            dataset_id=dataset_id,
            entries=d_entries
            ))

        def add_version(dataset):
            dataset['version'].append(dataset_version_id)

        Dataset = Query()
        self.datasets.update(add_version, Dataset.id == dataset_id)

        self.activity.insert(dict(user_id=user_id, dataset_id=dataset_id, message="Added version: {}".format(comments)))

        return dataset_version_id

def setup_user(db, name):
    home_folder_id = db.add_folder("{}'s Home".format(name), "home", "")
    trash_folder_id = db.add_folder("{}'s Trash".format(name), "trash", "")
    user_id = db.add_user(name, home_folder_id, trash_folder_id)
    return user_id

def open_db(filename):
    new_db = not os.path.exists(filename)

    db = TinyDB(filename)

    if new_db:
        #folders = db.table("folders")
        #setup_user(db, "admin")
        pass
    
    return Db(db)
