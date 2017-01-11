import pytest

from taiga2.controllers.models_controller import add_user, get_user

from taiga2.controllers.models_controller import add_folder, get_folder, update_folder_name, update_folder_description
from taiga2.controllers.models_controller import get_parent_folders

from taiga2.models import User, Folder
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


# Dataset

