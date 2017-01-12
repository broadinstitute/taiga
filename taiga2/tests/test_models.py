import pytest

from taiga2.controllers.models_controller import add_user, get_user

from taiga2.controllers.models_controller import add_folder, get_folder, update_folder_name, update_folder_description
from taiga2.controllers.models_controller import get_parent_folders, add_folder_entry, remove_folder_entry

from taiga2.controllers.models_controller import add_dataset

from taiga2.controllers.models_controller import get_entry

from taiga2.models import User, Folder, Dataset, Entry
from taiga2.models import generate_permaname

from flask_sqlalchemy import SessionBase


# User
@pytest.fixture
def new_user():
    _new_user = add_user(name="Remi")

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
    db_user = get_user(new_user.id)

    assert db_user == new_user


# Folder
@pytest.fixture
def new_folder(new_user):
    new_folder_name = "New folder"
    _new_folder = add_folder(creator_id=new_user.id,
                            name=new_folder_name,
                            folder_type=Folder.FolderType.folder,
                            description="Test new folder description")

    return _new_folder


@pytest.fixture
def new_dummy_folder(new_user):
    new_dummy_folder_name = "Dummy folder"
    _new_dummy_folder = add_folder(creator_id=new_user.id,
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
    added_folder = get_folder(new_folder.id)

    assert new_folder == added_folder


def test_update_folder_name(session: SessionBase, new_folder):
    new_folder_name = "New folder name"
    updated_folder = update_folder_name(folder_id=new_folder.id,
                                        new_name=new_folder_name)

    assert updated_folder.name == new_folder_name
    assert new_folder.name == new_folder_name


def test_update_folder_description(session: SessionBase, new_folder):
    new_folder_description = "New folder description"
    updated_folder = update_folder_description(new_folder.id, new_folder_description)

    assert updated_folder.description == new_folder_description
    assert new_folder.description == new_folder_description


def test_get_one_parent_folders(session: SessionBase,
                            new_folder,
                            new_dummy_folder):
    new_folder.entries.append(new_dummy_folder)

    parent_folders = get_parent_folders(new_dummy_folder.id)

    assert len(parent_folders) == 1
    assert parent_folders[0] == new_folder


def test_get_parent_folders(session: SessionBase,
                            new_user,
                            new_folder,
                            new_dummy_folder):
    folder_in_dummy_and_new_folder_folders = add_folder(creator_id=new_user.id,
                                                        name="Inception",
                                                        folder_type=Folder.FolderType.folder,
                                                        description="Folder inside two folders")
    # new_folder.entries.append(new_dummy_folder)
    new_folder.entries.append(folder_in_dummy_and_new_folder_folders)

    new_dummy_folder.entries.append(folder_in_dummy_and_new_folder_folders)

    parent_folders = get_parent_folders(folder_in_dummy_and_new_folder_folders.id)

    assert len(parent_folders) == 2
    assert new_folder in parent_folders
    assert new_dummy_folder in parent_folders


# TODO: Test also with a DatasetVersion
def test_add_folder_entry(session: SessionBase,
                          new_folder,
                          new_dummy_folder,
                          new_dataset):
    updated_folder = add_folder_entry(new_folder.id,
                                      new_dummy_folder.id)

    assert len(updated_folder.entries) == 1
    assert new_dummy_folder in updated_folder.entries

    updated_again_folder = add_folder_entry(new_folder.id,
                                            new_dataset.id)

    assert len(updated_again_folder.entries) == 2
    assert new_dataset in updated_again_folder.entries

    assert new_folder == updated_folder
    assert updated_again_folder == updated_folder


# Dataset
@pytest.fixture()
def new_dataset():
    new_dataset_name = "New Dataset"
    new_dataset_permaname = generate_permaname(new_dataset_name)

    _new_dataset = add_dataset(name=new_dataset_name,
                               permaname=new_dataset_permaname,
                               description="New dataset description")

    return _new_dataset


def test_add_dataset(session: SessionBase):
    new_dataset_name = "New Dataset"
    new_dataset_permaname = generate_permaname(new_dataset_name)

    _new_dataset = add_dataset(name=new_dataset_name,
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


# DatasetVersion

# Entry
def test_get_entry(session: SessionBase,
                   new_folder):
    entry = get_entry(new_folder.id)

    # TODO: Find why entry (new_folder) is not an Entry
    # assert type(entry) is Entry
    assert entry.id == new_folder.id
