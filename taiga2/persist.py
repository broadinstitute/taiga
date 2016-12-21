import os
import uuid
import collections
import re
import datetime
from tinydb import TinyDB, Query
import random
import sys

DatasetFile = collections.namedtuple("DatasetFile", "name description type datafile_id")

def new_id():
    return uuid.uuid4().hex

def now():
    return datetime.datetime.now().isoformat()

ALPHANUMS = [chr(x) for x in range(ord('a'), ord('z')+1)] + [chr(x) for x in range(ord('0'), ord('9')+1)]
def get_random_suffix(length):
    return "".join([ALPHANUMS[random.randint(0, len(ALPHANUMS)-1)] for i in range(length)])

class Db:
    def __init__(self, db):
        self.db = db
        self.users = db.table("users")
        self.folders = db.table("folders")
        self.datafiles = db.table("datafiles")
        self.datasets = db.table("datasets")
        self.dataset_versions = db.table("dataset_versions")
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

    def update_folder_description(self, folder_id, description):
        Folder = Query()
        self.folders.update(dict(description=description), Folder.id == folder_id)        

    def add_folder(self, creator_id, name, type, description):
        assert type in ['home', 'trash', 'folder']

        id = new_id()
        self.folders.insert(
            dict(id=id,
                name=name,
                type=type,
                description=description,
                entries=[],
                creator_id=creator_id,
                creation_date=now()))
        return id

    def get_folder(self, id):
        Folder = Query()
        return self.folders.get(Folder.id == id)

    def add_folder_entry(self, folder_id, id, type):
        assert type in ['folder', 'dataset', 'dataset_version']
        update_count = [0]
        def add_entry(f):
            for entry in f['entries']:
                if entry['id'] == id and entry['type'] == type:
                    return f
            f['entries'].append(dict(id=id, type=type))
            update_count[0] += 1
            return f

        Folder = Query()
        self.folders.update(add_entry, Folder.id == folder_id)
        if update_count[0] == 1:
            return True
        else:
            return False

    def remove_folder_entry(self, folder_id, id, type):
        update_count = [0]
        def remove_entry(f):
            before = len(f['entries'])
            f['entries'] = [entry for entry in f['entries'] if entry['id'] != id or entry['type'] != type]
            after = len(f['entries'])
            if before > after:
                update_count[0] += 1
            return f

        Folder = Query()
        self.folders.update(remove_entry, Folder.id == folder_id)
        if update_count[0] == 1:
            return True
        else:
            return False

    def get_folders_containing(self, id_type, id):
        def is_parent(entries):
            for e in entries:
                if e['type'] == id_type and e['id'] == id:
                    return True
            return False
        Folder = Query()
        parent_folders = self.folders.search(Folder.entries.test(is_parent))
        return parent_folders

    def get_parent_folders(self, folder_id):
        return self.get_folders_containing("folder", folder_id)

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
            type=e.type,
            url=get_url_for(e.datafile_id)
        ) for e in entries]

        return d_entries

    def create_dataset(self, user_id, name, description, entries, permaname=None):
        dataset_id = new_id()
        dataset_version_id = new_id()

        if permaname is None:
            # normalize 
            permaname=re.sub("[^a-z0-9]+", "-", name.lower())
            permaname=re.sub("-+", "-", permaname)
            permaname=re.sub("-$", "", permaname)
            permaname=re.sub("^-$", "", permaname)
            # append a random suffix to ensure uniqueness.  being purely random is a bug.
            # should really query and only pick a suffix which yields a permaname not already in
            # use.  This is just a prototype so skip that for now.
            suffix=get_random_suffix(2)
            permaname=permaname+"-"+suffix

        d_entries = self._convert_entries_to_dict(entries)

        self.datasets.insert(dict(
            id=dataset_id,
            name=name,
            description=description,
            versions=[dataset_version_id],
            permanames=[permaname]
            ))

        self.dataset_versions.insert(dict(
            id=dataset_version_id,
            dataset_id=dataset_id,
            entries=d_entries,
            creator_id=user_id,
            creation_date=now(),
            version="1",
            status="valid"
            ))

        self.activity.insert(dict(user_id=user_id, dataset_id=dataset_id, message="Created"))

        return dataset_version_id

    def update_dataset_name(self, user_id, dataset_id, name):
        Dataset = Query()
        self.datasets.update(dict(name=name), Dataset.id == dataset_id)        
        self.activity.insert(dict(user_id=user_id, dataset_id=dataset_id, message="Changed name"))

    def update_dataset_description(self, user_id, dataset_id, description):
        self.datasets.update(dict(description=description), Query().id == dataset_id)        
        self.activity.insert(dict(user_id=user_id, dataset_id=dataset_id, message="Changed description"))

    def update_datafile_summaries(self, dataset_version_id, datafile_name, content_summary):
        def update_summary(d):
            entries = d["entries"]
            with_name = [e for e in entries if e['name'] == datafile_name]
            for e in with_name:
                e['content_summary'] = content_summary
            return d
        self.dataset_versions.update(update_summary, Query().id == dataset_version_id)        

    def update_dataset_contents(self, user_id, dataset_id, entries_to_remove, entries_to_add, comments):
        for x in entries_to_remove:
            assert isinstance(x, str)
        for x in entries_to_add:
            assert isinstance(x, DatasetFile)

        Dataset = Query()
        dataset = self.datasets.get(Dataset.id == dataset_id)

        last_version_id = dataset['versions'][-1]

        DatasetVersion = Query()
        prev_dataset_versions = self.dataset_versions.search(DatasetVersion.id == last_version_id)
        prev_dataset_version = prev_dataset_versions[0]

        new_entries = dict([ (e['name'], e) for e in prev_dataset_version['entries'] if e['name'] not in entries_to_remove])
        d_entries = self._convert_entries_to_dict(entries_to_add)
        for e in d_entries:
            new_entries[e['name']] = e

        dataset_version_id = new_id()
        self.dataset_versions.insert(dict(
            id=dataset_version_id,
            dataset_id=dataset_id,
            entries=list(new_entries.values()),
            creator_id=user_id,
            creation_date=now(),
            version=str(len(dataset['versions']) + 1),
            status="valid"
            ))

        def add_version(dataset):
            dataset['versions'].append(dataset_version_id)

        Dataset = Query()
        self.datasets.update(add_version, Dataset.id == dataset_id)

        self.activity.insert(dict(user_id=user_id, dataset_id=dataset_id, message="Added version: {}".format(comments)))

        return dataset_version_id

    def get_dataset(self, dataset_id):
        Dataset = Query()
        return self.datasets.get(Dataset.id == dataset_id)
    
    def get_dataset_version(self, dataset_version_id):
        DatasetVersion = Query()
        return self.dataset_versions.get(DatasetVersion.id == dataset_version_id)

    def update_dataset_version_provenance(self, dataset_version_id, provenance):
        self.dataset_versions.update(dict(provenance=provenance), Query().id == dataset_version_id)

    def resolve_to_dataset(self, name):
        m = re.match("([^/:]+)$", name)
        if m is None:
            return None
        permaname = m.group(1)
        
        Dataset = Query()
        matches = self.datasets.search(Dataset.permaname == permaname)
        if len(matches) == 0:
            matches = self.datasets.search(Dataset.id == permaname)
            if len(matches) == 0:
                return None        
        
        dataset = matches[0]
        return dataset['id']

    def resolve_to_dataset_version(self, name):
        m = re.match("([^/:]+)(?::([0-9]+))?$", name)
        if m is None:
            return None
        permaname = m.group(1)
        version = m.group(2)
        
        dataset_id = self.resolve_to_dataset(permaname)
        if dataset_id is None:
            if self.get_dataset_version(permaname) is not None:
                return permaname
            else:
                return None
        
        dataset = self.get_dataset(dataset_id)
        # now look for version
        if version == "" or version is None:
            version = len(dataset['versions'])-1
        else:
            version = int(version)-1
        
        if version >= len(dataset['versions']):
            return None

        dataset_version_id = dataset['versions'][version]
        return dataset_version_id

    def resolve_to_datafile(self, name):
        m = re.match("([^/:]+(?::[0-9]+)?)(/.*)$", name)
        if m is None:
            return None
        dataset_name = m.group(1)
        path = m.group(2)

        dataset_version_id = self.resolve_to_dataset_version(dataset_name)
        if dataset_version_id is None:
            return None

        dataset_version = self.get_dataset_version(dataset_version_id)
        if path == "":
            path = dataset_version["entries"]["name"]

        entries = [e for e in dataset_version['entries'] if e['name'] == path]
        if len(entries) == 0:
            return None
        else:
            return entries[0]

def setup_user(db, name):
    home_folder_id = db.add_folder("admin", "{}'s Home".format(name), "home", "")
    trash_folder_id = db.add_folder("admin", "{}'s Trash".format(name), "trash", "")
    user_id = db.add_user(name, home_folder_id, trash_folder_id)
    return user_id

def open_db(filename):
    try:
        new_db = not os.path.exists(filename)

        db = TinyDB(filename, indent=2)

        if new_db:
            #folders = db.table("folders")
            #setup_user(db, "admin")
            print("No database found. Created a new one at %s" % filename)
    except:
        print("Exception while opening the database: %s" % sys.exc_info()[0])

    return Db(db)
