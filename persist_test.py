import collections
import pytest

from persist import open_db, setup_user, new_id
from persist import DatasetFile

Session = collections.namedtuple("Session", "db user user_id")

@pytest.fixture
def db_session(tmpdir):
    db, user, user_id = create_user_with_home_folder(tmpdir)
    return Session(db, user, user_id)

def create_user_with_home_folder(tmpdir):
    filename = str(tmpdir)+"/db.json"
    db = open_db(filename)
    user_id = setup_user(db, "user")
    user = db.get_user(user_id)
    return db, user, user_id

def test_setup_user(tmpdir):
    _, user, _ = create_user_with_home_folder(tmpdir)

    assert user['name'] == "user"
    assert user['home_folder_id'] is not None
    assert user['trash_folder_id'] is not None

def test_create_folder(db_session):
    user = db_session.user
    db = db_session.db
    home_folder_id = user['home_folder_id']

    home_folder = db.get_folder(home_folder_id)
    assert len(home_folder['entries']) == 0

    folder_id = db.add_folder("folder_name2", "folder", "description")
    db.add_folder_entry(home_folder_id, folder_id, "folder")

    parents = db.get_parent_folders(folder_id)
    assert len(parents) == 1

    home_folder = db.get_folder(home_folder_id)
    assert home_folder['entries'] == [ dict(type="folder", id=folder_id) ]

def create_child_folder(db_session, name):
    "Creates a folder in home folder"
    user = db_session.user
    db = db_session.db
    home_folder_id = user['home_folder_id']

    # create a folder so that we have something to remove
    folder_id = db.add_folder(name, "folder", name+" description")
    success = db.add_folder_entry(home_folder_id, folder_id, "folder")
    assert success

    # verify it's present now'
    home_folder = db.get_folder(home_folder_id)
    assert folder_id in [ x['id'] for x in home_folder['entries'] if x['type'] == 'folder' ]

    return folder_id

def test_remove_folder(db_session):
    user = db_session.user
    db = db_session.db
    home_folder_id = user['home_folder_id']

    folder_id = create_child_folder(db_session, "folder2")

    # remove folder
    success = db.remove_folder_entry(home_folder_id, folder_id, "folder")
    assert success
    home_folder = db.get_folder(home_folder_id)
    assert len(home_folder['entries']) == 0

def test_remove_nonexistant_folder(db_session):
    user = db_session.user
    db = db_session.db
    home_folder_id = user['home_folder_id']

    # remove an invalid folder id
    success = db.remove_folder_entry(home_folder_id, "bananas", "folder")
    assert not success
    home_folder = db.get_folder(home_folder_id)
    assert len(home_folder['entries']) == 0

def test_add_duplicate_folder(db_session):
    user = db_session.user
    db = db_session.db
    home_folder_id = user['home_folder_id']

    folder_id = create_child_folder(db_session, "folder2")

    # try adding again
    success = db.add_folder_entry(home_folder_id, folder_id, "folder")
    assert not success

    # folder should be unchanged
    home_folder = db.get_folder(home_folder_id)
    assert len(home_folder['entries']) == 1

def test_update_folder_name(db_session):
    user = db_session.user
    db = db_session.db

    folder_id = create_child_folder(db_session, "folder2")

    folder = db.get_folder(folder_id)
    assert folder['name'] == 'folder2'
    # update
    db.update_folder_name(folder_id, "folder3")
    folder = db.get_folder(folder_id)
    assert folder['name'] == 'folder3'

def test_update_folder_description(db_session):
    user = db_session.user
    db = db_session.db

    folder_id = create_child_folder(db_session, "folder2")

    folder = db.get_folder(folder_id)
    assert folder['description'] == 'folder2 description'
    # update
    db.update_folder_description(folder_id, "updated")
    folder = db.get_folder(folder_id)
    assert folder['description'] == 'updated'

def create_dataset(db_session, shortname=None, versions=1, filenames=["file"]):
    db = db_session.db
    dataset_files = []
    for filename in filenames:
        id = new_id()
        file_id = db.register_datafile_id(id, "http://"+filename)
        dataset_files.append( DatasetFile(filename, "filedesc", "type", id) )

    for v in range(versions):
        if v == 0:
            dataset_version_id = db.create_dataset(db_session.user_id, "name", "description", dataset_files, permaname=shortname)
            dataset_id = db.get_dataset_version(dataset_version_id)['dataset_id']
        else:
            dataset_version_id = db.update_dataset_contents(db_session.user_id, 
                dataset_id, [], dataset_files, "comments")

    return dataset_version_id

def test_create_and_add_to_dataset(db_session):
    user = db_session.user
    db = db_session.db
    home_folder_id = user['home_folder_id']

    # register a data file to be used by the dataset
    db.register_datafile_id("fileid", "http://file")
    db.register_datafile_id("fileid2", "http://file2")

    # create a dataset with a single datafile
    dataset_version_id = db.create_dataset(db_session.user_id, "name", "description", [DatasetFile("file", "filedesc", "type", "fileid")])

    # verify the dataset references the data file
    dataset_version = db.get_dataset_version(dataset_version_id)
    assert dataset_version['entries'] == [{'name': 'file', 'description': 'filedesc', 'type': 'type', 'url': 'http://file'}] 

    dataset_version_id = db.update_dataset_contents(db_session.user_id, dataset_version['dataset_id'], [], [DatasetFile("file", "updated", "type", "fileid2")], "comments")

    dataset_version = db.get_dataset_version(dataset_version_id)
    assert dataset_version['entries'] == [{'name': 'file', 'description': 'updated', 'type': 'type', 'url': 'http://file2'}] 

def test_create_and_remove_from_dataset(db_session):
    user = db_session.user
    db = db_session.db
    home_folder_id = user['home_folder_id']

    # register a data file to be used by the dataset
    db.register_datafile_id("fileid", "http://file")
    db.register_datafile_id("fileid2", "http://file2")

    # create a dataset with a single datafile
    dataset_version_id = db.create_dataset(db_session.user_id, "name", "description", 
        [DatasetFile("file", "filedesc", "type", "fileid"),
         DatasetFile("file2", "filedesc", "type", "fileid2")
        ])

    # verify the dataset references the data file
    dataset_version = db.get_dataset_version(dataset_version_id)
    dataset_version_id = db.update_dataset_contents(db_session.user_id, dataset_version['dataset_id'], ["file"], [], "comments")

    dataset_version = db.get_dataset_version(dataset_version_id)
    assert dataset_version['entries'] == [{'name': 'file2', 'description': 'filedesc', 'type': 'type', 'url': 'http://file2'}] 

def test_dataset_update_name(db_session):
    db = db_session.db
    user_id = db_session.user['id']
    db.register_datafile_id("fileid", "http://file")
    dataset_version_id = db.create_dataset(db_session.user_id, "name", "description", [DatasetFile("file", "filedesc", "type", "fileid")])
    dataset_id = db.get_dataset_version(dataset_version_id)['dataset_id']
    dataset = db.get_dataset(dataset_id)
    assert dataset['name'] == "name"

    db.update_dataset_name(user_id, dataset_id, "name2")    
    dataset = db.get_dataset(dataset_id)
    assert dataset['name'] == "name2"

def test_dataset_update_description(db_session):
    db = db_session.db
    user_id = db_session.user['id']
    db.register_datafile_id("fileid", "http://file")
    dataset_version_id = db.create_dataset(db_session.user_id, "name", "description", [DatasetFile("file", "filedesc", "type", "fileid")])
    dataset_id = db.get_dataset_version(dataset_version_id)['dataset_id']
    dataset = db.get_dataset(dataset_id)
    assert dataset['description'] == "description"

    db.update_dataset_description(user_id, dataset_id, "description2")    
    dataset = db.get_dataset(dataset_id)
    assert dataset['description'] == "description2"


def test_resolve_to_dataset(db_session):
    db = db_session.db

    dataset_version_id = create_dataset(db_session, shortname="short")
    dataset_id = db.get_dataset_version(dataset_version_id)['dataset_id']

    assert dataset_id == db.resolve_to_dataset("short")
    assert dataset_id == db.resolve_to_dataset(dataset_id)
    assert db.resolve_to_dataset("missing") is None

def test_resolve_to_dataset_version(db_session):
    db = db_session.db

    dataset_version_id = create_dataset(db_session, shortname="short", versions=2)
    dataset_id = db.get_dataset_version(dataset_version_id)['dataset_id']

    assert dataset_version_id == db.resolve_to_dataset_version("short")
    assert dataset_version_id == db.resolve_to_dataset_version(dataset_id)
    assert dataset_version_id == db.resolve_to_dataset_version(dataset_version_id)
    assert dataset_version_id == db.resolve_to_dataset_version("short:2")
    assert db.resolve_to_dataset_version("missing") is None

@pytest.mark.skip(reason="resolve_to_dataset returns object")
def test_resolve_to_datafile(db_session):
    db = db_session.db

    dataset_id = create_dataset(db_session, shortname="short", versions=2, filenames=["file"])
    dataset_id = db.get_dataset_version(dataset_version_id)['dataset_id']

    assert (dataset_version_id, "file") == db.resolve_to_dataset_version("short")
    assert (dataset_version_id, "file") == db.resolve_to_dataset_version(dataset_id)
    assert (dataset_version_id, "file") == db.resolve_to_dataset_version(dataset_version_id)
    assert (dataset_version_id, "file") == db.resolve_to_dataset_version("short:1")
    assert (dataset_version_id, "file") == db.resolve_to_dataset_version("short/file")
    assert (dataset_version_id, "file") == db.resolve_to_dataset_version("short:1/file")
    assert db.resolve_to_dataset_version("missing") is None

# tests: 
# add_folder_entry:
#   error if same folder/dataset/datasetversion added twice to folder
#   error if dataset and datasetversion added to folder
# remove_folder:
#   error if attempt to remove missing folder/dataset/version from folder
# create dataset
#   error if references non-existant DatasetFile
#   error when adding two files with same name
# update dataset
#   error when removing non-existant entry
# update_dataset_name, update_dataset_description, update_folder_name, update_folder_description
# (add to api) get_activity(dataset_id)
# (add to api) get dataset file url(permaname|dataset_version_id|dataset_id)
# resolve_to_datafile(name) -> dataset_version_id, filename | error
# create dataset should return an import id and status.  Add additional operation for polling new status

