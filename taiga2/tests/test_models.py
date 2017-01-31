import datetime
import pytest

from freezegun import freeze_time
from flask_sqlalchemy import SessionBase

import taiga2.controllers.models_controller as mc

from taiga2.models import db
from taiga2.models import User, Folder, Dataset, DatasetVersion
from taiga2.models import generate_permaname

# TODO: Remove the domain tests and bring them to test_domain.py
#<editor-fold desc="User Tests">
@pytest.fixture
def new_user():
    _new_user = mc.get_user(1)
    if not _new_user:
        _new_user = mc.add_user(name="Remi")

    return _new_user


def test_add_user(session, new_user):
    new_user_name = "Remi"

    # Retrieve the user to see if we get what we are supposed
    # to have stored
    added_user = session.query(User).filter(User.name == new_user_name).first()

    assert new_user.id == added_user.id
    assert new_user.name == added_user.name
    assert new_user.home_folder.name == added_user.home_folder.name


def test_get_user(session, new_user):
    db_user = mc.get_user(new_user.id)

    assert db_user == new_user
#</editor-fold>

#<editor-fold desc="SessionUpload">
def test_create_sessionUpload(session: SessionBase):
    sessionUpload = mc.UploadSession()

    assert isinstance(sessionUpload, mc.UploadSession)
#</editor-fold>

#<editor-fold desc="Folder Tests">
@pytest.fixture
def new_folder(new_user):
    new_folder_name = "New folder"
    _new_folder = mc.add_folder(creator_id=new_user.id,
                            name=new_folder_name,
                            folder_type=Folder.FolderType.folder,
                            description="Test new folder description")

    return _new_folder


@pytest.fixture
def new_dummy_folder(new_user):
    new_dummy_folder_name = "Dummy folder"
    _new_dummy_folder = mc.add_folder(creator_id=new_user.id,
                                   name=new_dummy_folder_name,
                                   folder_type=Folder.FolderType.home,
                                   description="I am a dummy folder for testing purpose")

    return _new_dummy_folder


# TODO: Test multiple types of folders, depending on the populated attributes
def test_add_folder(session: SessionBase, new_user, new_folder):
    added_folder = session.query(Folder) \
        .filter(Folder.name == new_folder.name and User.name == new_user.name) \
        .one()

    assert new_folder == added_folder


def test_get_folder(session: SessionBase, new_folder):
    added_folder = mc.get_folder(new_folder.id)

    assert new_folder == added_folder


def test_update_folder_name(session: SessionBase, new_folder):
    new_folder_name = "New folder name"
    updated_folder = mc.update_folder_name(folder_id=new_folder.id,
                                        new_name=new_folder_name)

    assert updated_folder.name == new_folder_name
    assert new_folder.name == new_folder_name


def test_update_folder_description(session: SessionBase, new_folder):
    new_folder_description = "New folder description"
    updated_folder = mc.update_folder_description(new_folder.id, new_folder_description)

    assert updated_folder.description == new_folder_description
    assert new_folder.description == new_folder_description


def test_get_one_parent_folders(session: SessionBase,
                            new_folder,
                            new_dummy_folder):
    new_folder.entries.append(new_dummy_folder)

    parent_folders = mc.get_parent_folders(new_dummy_folder.id)

    assert len(parent_folders) == 1
    assert parent_folders[0] == new_folder


def test_get_parent_folders(session: SessionBase,
                            new_user,
                            new_folder,
                            new_dummy_folder):
    folder_in_dummy_and_new_folder_folders = mc.add_folder(creator_id=new_user.id,
                                                        name="Inception",
                                                        folder_type=Folder.FolderType.folder,
                                                        description="Folder inside two folders")
    # new_folder.entries.append(new_dummy_folder)
    new_folder.entries.append(folder_in_dummy_and_new_folder_folders)

    new_dummy_folder.entries.append(folder_in_dummy_and_new_folder_folders)

    parent_folders = mc.get_parent_folders(folder_in_dummy_and_new_folder_folders.id)

    assert len(parent_folders) == 2
    assert new_folder in parent_folders
    assert new_dummy_folder in parent_folders


# TODO: Test also with a DatasetVersion
def test_add_folder_entry(session: SessionBase,
                          new_folder,
                          new_dummy_folder,
                          new_dataset):
    updated_folder = mc.add_folder_entry(new_folder.id,
                                      new_dummy_folder.id)

    assert len(updated_folder.entries) == 1
    assert new_dummy_folder in updated_folder.entries

    updated_again_folder = mc.add_folder_entry(new_folder.id,
                                            new_dataset.id)

    assert len(updated_again_folder.entries) == 2
    assert new_dataset in updated_again_folder.entries

    assert new_folder == updated_folder
    assert updated_again_folder == updated_folder
#</editor-fold>

#<editor-fold desc="Dataset Tests">
@pytest.fixture()
def new_dataset():
    new_dataset_name = "New Dataset"
    new_dataset_permaname = generate_permaname(new_dataset_name)

    _new_dataset = mc.add_dataset(name=new_dataset_name,
                               permaname=new_dataset_permaname,
                               description="New dataset description")

    return _new_dataset


def test_add_dataset(session: SessionBase):
    new_dataset_name = "New Dataset"
    new_dataset_permaname = generate_permaname(new_dataset_name)

    _new_dataset = mc.add_dataset(name=new_dataset_name,
                               permaname=new_dataset_permaname,
                               description="New dataset description")

    added_dataset_by_id = session.query(Dataset) \
        .filter(Dataset.id == _new_dataset.id) \
        .one()

    added_dataset_by_permaname = session.query(Dataset) \
        .filter(Dataset.permaname == _new_dataset.permaname) \
        .one()

    # Ensure the object we put in the database is the same than the one
    # we get by id
    assert added_dataset_by_id == _new_dataset
    assert added_dataset_by_id.name == new_dataset_name
    assert added_dataset_by_id.permaname == new_dataset_permaname

    # Also ensure that we have a unique permaname and it is the right one
    assert added_dataset_by_permaname == _new_dataset


def test_add_dataset_with_datafile(session: SessionBase,
                                          new_user,
                                          new_datafile):
    new_dataset_name = "New dataset with datasetVersion"
    new_dataset_description = "New dataset with datasetVersion"

    datafiles_ids = [new_datafile.id]

    new_dataset = mc.add_dataset(name=new_dataset_name,
                              creator_id=new_user.id,
                              description=new_dataset_description,
                              datafiles_ids=datafiles_ids)

    assert new_dataset.name == new_dataset_name
    assert new_dataset.description == new_dataset_description
    assert len(new_dataset.dataset_versions) == 1

    assert len(new_dataset.dataset_versions[0].datafiles) == 1
    assert new_dataset.dataset_versions[0].datafiles[0] == new_datafile


def test_update_dataset_name(session: SessionBase,
                             new_dataset):
    new_dataset_name = "New name"
    updated_dataset = mc.update_dataset_name(new_dataset.id,
                                          new_dataset_name)

    assert new_dataset == updated_dataset
    assert updated_dataset.name == new_dataset_name


def test_update_dataset_description(session: SessionBase,
                                    new_dataset):
    new_dataset_description = "New description"
    updated_dataset = mc.update_dataset_description(new_dataset.id,
                                                 new_dataset_description)

    assert updated_dataset == new_dataset
    assert updated_dataset.description == new_dataset_description


def test_update_dataset_contents(session: SessionBase,
                                 new_dataset_version,
                                 new_datafile):
    _new_dataset = new_dataset_version.dataset
    # TODO: This test showed an issue with the conftest.py with session on db fixture. Temp fix with function as scope which destroys db
    # TODO: Replace this with a fixture or a direct call to a function
    # new_dataset = new_dataset_version.dataset
    # Add one datafile to begin with
    new_dataset_version.datafiles.append(new_datafile)
    session.add(new_dataset_version)
    session.commit()

    entries_to_remove = [new_datafile.id]
    updated_dataset = mc.update_dataset_contents(_new_dataset.id,
                                              datafiles_id_to_remove=entries_to_remove)

    last_dataset_version = mc.get_latest_dataset_version(updated_dataset.id)

    assert updated_dataset == _new_dataset
    assert last_dataset_version.version == new_dataset_version.version + 1
    assert len(updated_dataset.dataset_versions) == 2
    assert len(last_dataset_version.datafiles) == 0

    entries_to_add = [new_datafile.id]
    updated_added_dataset = mc.update_dataset_contents(_new_dataset.id,
                                                    datafiles_id_to_add=entries_to_add)

    new_last_dataset_version = mc.get_latest_dataset_version(updated_added_dataset.id)

    assert updated_added_dataset == updated_dataset
    assert len(updated_added_dataset.dataset_versions) == 3
    assert len(new_last_dataset_version.datafiles) == 1


def test_get_dataset(session: SessionBase,
                     new_dataset):
    fetched_dataset = mc.get_dataset(new_dataset.id)

    assert fetched_dataset == new_dataset
    assert fetched_dataset.id == new_dataset.id


def test_get_dataset_by_permaname(session: SessionBase,
                                  new_dataset: Dataset):
    fetched_dataset = mc.get_dataset_from_permaname(new_dataset.permaname)

    assert fetched_dataset == new_dataset
    assert fetched_dataset.id == new_dataset.id
    assert fetched_dataset.permaname == new_dataset.permaname

#</editor-fold>

#<editor-fold desc="DatasetVersion Tests">
@pytest.fixture
def new_dataset_version():
    # TODO: Add in the name it is an empty dataset_version
    new_dataset_version_name = "New Dataset Version"

    _new_user = new_user()
    _new_dataset = new_dataset()

    _new_dataset_version = DatasetVersion(name=new_dataset_version_name,
                                          creator=_new_user,
                                          dataset=_new_dataset,
                                          version=1)

    db.session.add(_new_dataset_version)
    db.session.commit()

    return _new_dataset_version


def test_add_dataset_version(session: SessionBase,
                             new_user,
                             new_dataset):
    new_dataset_version_name = "New Dataset Version"

    new_dataset_version = mc.add_dataset_version(name=new_dataset_version_name,
                                              creator_id=new_user.id,
                                              dataset_id=new_dataset.id)

    assert new_dataset_version.name == new_dataset_version_name
    assert new_dataset_version.creator == new_user
    assert new_dataset_version.dataset == new_dataset
    # TODO: Be careful with timezone between the database and the testing machine
    # assert new_dataset_version.creation_date.date() == datetime.datetime.now().date()


def test_get_dataset_version(session,
                             new_dataset_version):
    fetched_dataset_version = mc.get_dataset_version(new_dataset_version.id)

    assert fetched_dataset_version == new_dataset_version
    assert fetched_dataset_version.id == new_dataset_version.id

def test_get_dataset_version_by_permaname_and_version(session,
                                                      new_dataset_version: DatasetVersion):
    dataset = new_dataset_version.dataset
    first_version_number = 1
    first_dataset_version = mc.get_dataset_version_by_permaname_and_version(dataset.permaname,
                                                                              first_version_number)

    check_first_dataset_version = [dataset_version
                                   for dataset_version in dataset.dataset_versions
                                   if dataset_version.version == 1][0]
    assert first_dataset_version == check_first_dataset_version
    assert first_dataset_version.version == 1

def test_get_dataset_version_by_dataset_id_and_dataset_version_id(session: SessionBase,
                                                                  new_dataset,
                                                                  new_dataset_version):

    _dataset_version_id = new_dataset_version.dataset_id

    test_dataset_version = mc.get_dataset_version_by_dataset_id_and_dataset_version_id(_dataset_version_id,
                                                                                    new_dataset_version.id)

    assert test_dataset_version == new_dataset_version


#</editor-fold>

#<editor-fold desc="DataFile Tests">
@pytest.fixture
def new_datafile():
    new_datafile_name = "New Datafile"
    new_datafile_permaname = generate_permaname(new_datafile_name)

    new_datafile_url = "http://google.com"

    _new_datafile = mc.add_datafile(name=new_datafile_name,
                                 url=new_datafile_url)

    return _new_datafile
#</editor-fold>

#<editor-fold desc="Entry Tests">

def test_get_entry(session: SessionBase,
                   new_folder):
    entry = mc.get_entry(new_folder.id)

    # TODO: Find why entry (new_folder) is not an Entry
    # assert type(entry) is Entry
    assert entry.id == new_folder.id

#</editor-fold>

#<editor-fold desc="Test Utilities">
# TODO: Test generate_name
#</editor-fold>

