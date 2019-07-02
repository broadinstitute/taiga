import datetime
import pytest
import uuid

from flask_sqlalchemy import SessionBase

import flask

import taiga2.controllers.models_controller as mc
from taiga2.controllers.models_controller import DataFileAlias

from taiga2.models import db
from taiga2.models import User, Folder, Dataset, DatasetVersion, Group, S3DataFile
from taiga2.models import generate_permaname
from taiga2.models import DataFile
from taiga2.models import EntryRightsEnum

from taiga2.tests.test_endpoint import (
    add_version,
    new_upload_session_file,
    new_upload_session,
)


# from taiga2.tests.factories import GroupFactory, UserFactory, FolderFactory


# TODO: Remove the domain tests and bring them to test_endpoint.py
# <editor-fold desc="User Tests">

# TODO: These two tests generate Integrity error on the token. Why? Due to the way a uuid is generated during the tests?
# @pytest.fixture(scope='function')
# def new_user():
#     print("Our users before {}".format(mc.get_all_users()))
#     new_user_name = str(uuid.uuid4())
#     new_user_email = new_user_name + "@broadinstitute.org"
#     _new_user = mc.add_user(name=new_user_name,
#                             email=new_user_email)
#     print("Our users after {}".format(mc.get_all_users()))
#     return _new_user
#
#
# def test_add_user(session):
#     new_user_name = str(uuid.uuid4())
#     new_user_email = new_user_name + "@broadinstitute.org"
#     _new_user = mc.add_user(name=new_user_name,
#                             email=new_user_email)
#
#     # Retrieve the user to see if we get what we are supposed
#     # to have stored
#     added_user = session.query(User).filter(User.name == new_user_name).first()
#
#     assert _new_user.id == added_user.id
#     assert _new_user.name == added_user.name
#     assert _new_user.home_folder.name == added_user.home_folder.name


def test_get_user(session):
    current_user = flask.g.current_user
    db_user = mc.get_user(current_user.id)

    assert db_user == current_user


# </editor-fold>

# <editor-fold desc="SessionUpload">
def test_create_sessionUpload(session: SessionBase):
    sessionUpload = mc.UploadSession()

    assert isinstance(sessionUpload, mc.UploadSession)


# </editor-fold>

# <editor-fold desc="Folder Tests">
@pytest.fixture
def new_folder():
    new_folder_name = "New folder"
    _new_folder = mc.add_folder(
        name=new_folder_name,
        folder_type=Folder.FolderType.folder,
        description="Test new folder description",
    )

    return _new_folder


@pytest.fixture
def new_dummy_folder():
    new_dummy_folder_name = "Dummy folder"
    _new_dummy_folder = mc.add_folder(
        name=new_dummy_folder_name,
        folder_type=Folder.FolderType.home,
        description="I am a dummy folder for testing purpose",
    )

    return _new_dummy_folder


# TODO: Test multiple types of folders, depending on the populated attributes
def test_add_folder(session: SessionBase, new_folder):
    current_user = flask.g.current_user
    added_folder = (
        session.query(Folder)
        .filter(Folder.name == new_folder.name and User.name == current_user.name)
        .one()
    )

    assert new_folder == added_folder


def test_get_folder(session: SessionBase, new_folder):
    added_folder = mc.get_folder(new_folder.id)

    assert new_folder == added_folder


def test_update_folder_name(session: SessionBase, new_folder):
    new_folder_name = "New folder name"
    updated_folder = mc.update_folder_name(
        folder_id=new_folder.id, new_name=new_folder_name
    )

    assert updated_folder.name == new_folder_name
    assert new_folder.name == new_folder_name


def test_update_folder_description(session: SessionBase, new_folder):
    new_folder_description = "New folder description"
    updated_folder = mc.update_folder_description(new_folder.id, new_folder_description)

    assert updated_folder.description == new_folder_description
    assert new_folder.description == new_folder_description


def test_get_one_parent_folders(session: SessionBase, new_folder, new_dummy_folder):
    new_folder.entries.append(new_dummy_folder)

    parent_folders = mc.get_parent_folders(new_dummy_folder.id)

    assert len(parent_folders) == 1
    assert parent_folders[0] == new_folder


def test_get_parent_folders(session: SessionBase, new_folder, new_dummy_folder):
    folder_in_dummy_and_new_folder_folders = mc.add_folder(
        name="Inception",
        folder_type=Folder.FolderType.folder,
        description="Folder inside two folders",
    )
    # new_folder.entries.append(new_dummy_folder)
    new_folder.entries.append(folder_in_dummy_and_new_folder_folders)

    new_dummy_folder.entries.append(folder_in_dummy_and_new_folder_folders)

    parent_folders = mc.get_parent_folders(folder_in_dummy_and_new_folder_folders.id)

    assert len(parent_folders) == 2
    assert new_folder in parent_folders
    assert new_dummy_folder in parent_folders


# TODO: Test also with a DatasetVersion
def test_add_folder_entry(
    session: SessionBase, new_folder, new_dummy_folder, new_dataset
):
    updated_folder = mc.add_folder_entry(new_folder.id, new_dummy_folder.id)

    assert len(updated_folder.entries) == 1
    assert new_dummy_folder in updated_folder.entries

    updated_again_folder = mc.add_folder_entry(new_folder.id, new_dataset.id)

    assert len(updated_again_folder.entries) == 2
    assert new_dataset in updated_again_folder.entries

    assert new_folder == updated_folder
    assert updated_again_folder == updated_folder


# </editor-fold>

# <editor-fold desc="Dataset Tests">
@pytest.fixture()
def new_dataset(new_datafile):
    new_dataset_name = "New Dataset"
    new_dataset_permaname = generate_permaname(new_dataset_name)

    _new_dataset = mc.add_dataset(
        name=new_dataset_name,
        permaname=new_dataset_permaname,
        description="New dataset description",
        datafiles_ids=[new_datafile.id],
    )

    return _new_dataset


def test_add_dataset(session: SessionBase, new_datafile):
    new_dataset_name = "New Dataset"
    new_dataset_permaname = generate_permaname(new_dataset_name)

    _new_dataset = mc.add_dataset(
        name=new_dataset_name,
        permaname=new_dataset_permaname,
        description="New dataset description",
        datafiles_ids=[new_datafile.id],
    )

    added_dataset_by_id = (
        session.query(Dataset).filter(Dataset.id == _new_dataset.id).one()
    )

    added_dataset_by_permaname = (
        session.query(Dataset).filter(Dataset.permaname == _new_dataset.permaname).one()
    )

    # Ensure the object we put in the database is the same than the one
    # we get by id
    assert added_dataset_by_id == _new_dataset
    assert added_dataset_by_id.name == new_dataset_name
    assert added_dataset_by_id.permaname == new_dataset_permaname

    # Also ensure that we have a unique permaname and it is the right one
    assert added_dataset_by_permaname == _new_dataset


def test_add_dataset_with_datafile(session: SessionBase, new_datafile):
    new_dataset_name = "New dataset with datasetVersion"
    new_dataset_description = "New dataset with datasetVersion"

    datafiles_ids = [new_datafile.id]

    new_dataset = mc.add_dataset(
        name=new_dataset_name,
        description=new_dataset_description,
        datafiles_ids=datafiles_ids,
    )

    assert new_dataset.name == new_dataset_name
    assert new_dataset.description == new_dataset_description
    assert len(new_dataset.dataset_versions) == 1

    assert len(new_dataset.dataset_versions[0].datafiles) == 1
    assert new_dataset.dataset_versions[0].datafiles[0] == new_datafile


def test_update_dataset_name(session: SessionBase, new_dataset):
    new_dataset_name = "New name"
    updated_dataset = mc.update_dataset_name(new_dataset.id, new_dataset_name)

    assert new_dataset == updated_dataset
    assert updated_dataset.name == new_dataset_name


def test_update_dataset_description(session: SessionBase, new_dataset):
    new_dataset_description = "New description"
    updated_dataset = mc.update_dataset_description(
        new_dataset.id, new_dataset_description
    )

    assert updated_dataset == new_dataset
    assert updated_dataset.description == new_dataset_description


# TODO: Deactivated for now since we are not yet doing updates
# def test_update_dataset_contents(session: SessionBase,
#                                  new_dataset,
#                                  new_datafile):
#     # TODO: This test showed an issue with the conftest.py with session on db fixture. Temp fix with function as scope which destroys db
#     # TODO: Replace this with a fixture or a direct call to a function
#     # new_dataset = new_dataset_version.dataset
#     # Add one datafile to begin with
#     new_dataset_version.datafiles.append(new_datafile)
#     session.add(new_dataset_version)
#     session.flush()
#
#     entries_to_remove = [new_datafile.id]
#     updated_dataset = mc.update_dataset_contents(_new_dataset.id,
#                                                  datafiles_id_to_remove=entries_to_remove)
#
#     last_dataset_version = mc.get_latest_dataset_version(updated_dataset.id)
#
#     assert updated_dataset == _new_dataset
#     assert last_dataset_version.version == new_dataset_version.version + 1
#     assert len(updated_dataset.dataset_versions) == 2
#     assert len(last_dataset_version.datafiles) == 0
#
#     entries_to_add = [new_datafile.id]
#     updated_added_dataset = mc.update_dataset_contents(_new_dataset.id,
#                                                        datafiles_id_to_add=entries_to_add)
#
#     new_last_dataset_version = mc.get_latest_dataset_version(updated_added_dataset.id)
#
#     assert updated_added_dataset == updated_dataset
#     assert len(updated_added_dataset.dataset_versions) == 3
#     assert len(new_last_dataset_version.datafiles) == 1


def test_get_dataset(session: SessionBase, new_dataset):
    fetched_dataset = mc.get_dataset(new_dataset.id)

    assert fetched_dataset == new_dataset
    assert fetched_dataset.id == new_dataset.id


def test_get_dataset_by_permaname(session: SessionBase, new_dataset: Dataset):
    fetched_dataset = mc.get_dataset_from_permaname(new_dataset.permaname)

    assert fetched_dataset == new_dataset
    assert fetched_dataset.id == new_dataset.id
    assert fetched_dataset.permaname == new_dataset.permaname


# </editor-fold>

# <editor-fold desc="DatasetVersion Tests">
@pytest.fixture
def new_dataset_version(new_datafile):
    # TODO: Add in the name it is an empty dataset_version
    new_dataset_name = "New Dataset for new_dataset_version"
    new_dataset_description = "New description for new_dataset_version"

    _new_dataset = mc.add_dataset(
        name=new_dataset_name,
        description=new_dataset_description,
        datafiles_ids=[new_datafile.id],
    )

    _new_dataset_version = _new_dataset.dataset_versions[0]

    return _new_dataset_version


def test_add_dataset_version(session: SessionBase):
    new_dataset_version_name = "New Dataset Version"

    new_dataset_name = "New Dataset for test_add_dataset_version"
    new_dataset_description = "New description for test_add_dataset_version"
    _new_datafile = mc.add_s3_datafile(
        name="Datafile for test_add_dataset_version",
        s3_bucket="broadtaiga2prototype",
        s3_key=mc.generate_convert_key(),
        type=mc.S3DataFile.DataFileFormat.Raw,
        short_summary="short",
        long_summary="long",
    )

    _new_dataset = mc.add_dataset(
        name=new_dataset_version_name,
        description=new_dataset_description,
        datafiles_ids=[_new_datafile.id],
    )

    _new_dataset_version = _new_dataset.dataset_versions[0]

    _new_dataset_version.datafiles.append(_new_datafile)

    db.session.add(_new_dataset_version)
    db.session.commit()

    return _new_dataset_version

    assert new_dataset_version.name == new_dataset_version_name
    assert new_dataset_version.creator == flask.g.current_user
    assert new_dataset_version.dataset == new_dataset
    assert new_dataset_version.state == DatasetVersion.DatasetVersionState.approved
    # TODO: Be careful with timezone between the database and the testing machine
    # assert new_dataset_version.creation_date.date() == datetime.datetime.now().date()


def test_get_dataset_version(session, new_dataset_version):
    fetched_dataset_version = mc.get_dataset_version(new_dataset_version.id)

    assert fetched_dataset_version == new_dataset_version
    assert fetched_dataset_version.id == new_dataset_version.id


def test_get_dataset_version_by_permaname_and_version(
    session, new_dataset_version: DatasetVersion
):
    dataset = new_dataset_version.dataset
    first_version_number = 1
    first_dataset_version = mc.get_dataset_version_by_permaname_and_version(
        dataset.permaname, first_version_number
    )

    check_first_dataset_version = [
        dataset_version
        for dataset_version in dataset.dataset_versions
        if dataset_version.version == 1
    ][0]
    assert first_dataset_version == check_first_dataset_version
    assert first_dataset_version.version == 1


def test_get_dataset_version_by_dataset_id_and_dataset_version_id(
    session: SessionBase, new_dataset, new_dataset_version
):
    _dataset_version_id = new_dataset_version.dataset_id

    test_dataset_version = mc.get_dataset_version_by_dataset_id_and_dataset_version_id(
        _dataset_version_id, new_dataset_version.id
    )

    assert test_dataset_version == new_dataset_version


def test_state_approved_to_deprecated(
    session: SessionBase, new_dataset, new_dataset_version
):
    assert new_dataset_version.state == DatasetVersion.DatasetVersionState.approved

    dataset_version_id = new_dataset_version.id
    mc.deprecate_dataset_version(dataset_version_id, "test deprecation")

    updated_dataset_version = mc.get_dataset_version(
        dataset_version_id=dataset_version_id
    )

    assert (
        updated_dataset_version.state == DatasetVersion.DatasetVersionState.deprecated
    )


def test_state_deprecated_to_approved(
    session: SessionBase, new_dataset, new_dataset_version
):
    dataset_version_id = new_dataset_version.id

    # TODO: Might not be the best way to test this, since we rely on the deprecation function to work
    mc.deprecate_dataset_version(new_dataset_version.id, "test deprecation")

    assert new_dataset_version.state == DatasetVersion.DatasetVersionState.deprecated

    mc.approve_dataset_version(dataset_version_id)

    assert new_dataset_version.state == DatasetVersion.DatasetVersionState.approved


def test_state_to_deleted(session: SessionBase, new_dataset, new_dataset_version):
    # TODO: Could benefit of parametrizing the state of the datasetVersion in case some switch are not allowed
    dataset_version_id = new_dataset_version.id
    mc.delete_dataset_version(dataset_version_id)

    updated_dataset_version = mc.get_dataset_version(
        dataset_version_id=dataset_version_id
    )

    assert updated_dataset_version.state == DatasetVersion.DatasetVersionState.deleted


# </editor-fold>

# <editor-fold desc="DataFile Tests">
@pytest.fixture
def new_datafile():
    new_datafile_name = "New Datafile"
    new_datafile_url = "http://google.com"

    _new_datafile = mc.add_s3_datafile(
        name=new_datafile_name,
        s3_bucket="broadtaiga2prototype",
        s3_key=mc.generate_convert_key(),
        type=S3DataFile.DataFileFormat.Raw,
        short_summary="short",
        long_summary="long",
    )

    return _new_datafile


# </editor-fold>

# <editor-fold desc="Entry Tests">


def test_get_entry(session: SessionBase, new_folder):
    entry = mc.get_entry(new_folder.id)

    # TODO: Find why entry (new_folder) is not an Entry
    # assert type(entry) is Entry
    assert entry.id == new_folder.id


# </editor-fold>

# <editor-fold desc="Provenance Tests">


def test_add_provenance_graph(session: SessionBase):
    graph_permaname = "permaname_graph"
    graph_name = "Graph name"
    graph_user_id = flask.g.current_user.id
    graph_id = graph_permaname

    _new_graph = mc.add_graph(
        graph_permaname=graph_permaname,
        graph_name=graph_name,
        graph_user_id=graph_user_id,
        graph_id=graph_id,
    )

    return _new_graph


@pytest.fixture
def new_graph():
    graph_permaname = "permaname_graph"
    graph_name = "Graph name"
    graph_user_id = flask.g.current_user.id
    graph_id = graph_permaname

    _new_graph = mc.add_graph(
        graph_permaname=graph_permaname,
        graph_name=graph_name,
        graph_user_id=graph_user_id,
        graph_id=graph_id,
    )

    return _new_graph


def test_get_provenance_graph(session: SessionBase, new_graph):
    _test_graph = mc.get_provenance_graph(new_graph.graph_id)

    assert _test_graph.graph_id == new_graph.graph_id


# TODO: Implement node and edge tests
# def test_add_provenance_node(session: SessionBase):
#     return False
#
#
# def test_get_provenance_node(session: SessionBase):
#     return False
#
#
# def test_add_provenance_edge(session: SessionBase):
#     return False
#
#
# def test_get_provenance_edge(session: SessionBase):
#     return False

# </editor-fold>

# <editor-fold desc="Group">


# def test_new_group(session: SessionBase):
#     name = "New group"
#     new_group = GroupFactory(name=name)
#
#     assert new_group.name == name


def test_admin_group_exists(session: SessionBase):
    get_groups = mc.get_all_groups()

    assert len(get_groups) != 0


def test_add_group_user_association(session: SessionBase):
    new_user = mc.add_user("test", "test@group.com")

    new_group = mc.add_group("test")
    new_group.users.append(new_user)

    assert new_user in new_group.users


def test_view_not_owned(session: SessionBase):
    new_user = mc.add_user("test", "test@group.com")
    flask.g.current_user = new_user

    new_user_not_tested = mc.add_user("test_useless", "test_useless@group.com")

    # new_folder_not_owned = FolderFactory(creator=new_user_not_tested)
    new_folder_not_owned = mc.add_folder(
        name="folder_not_owned", folder_type=Folder.FolderType.folder, description=""
    )
    new_folder_not_owned.creator = new_user_not_tested

    right_not_owned = mc.get_rights(new_folder_not_owned.id)

    assert right_not_owned == EntryRightsEnum.can_view


def test_edit_owned(session: SessionBase):
    new_user = mc.add_user("test", "test@group.com")
    flask.g.current_user = new_user

    # new_folder_owned = FolderFactory(creator=new_user)
    new_folder_owned = mc.add_folder(
        name="Test folder", folder_type=Folder.FolderType.folder, description=""
    )

    right_owned = mc.get_rights(new_folder_owned.id)

    assert right_owned == EntryRightsEnum.can_edit


# </editor-fold>

# <editor-fold desc="Test Utilities">
# TODO: Test generate_name
# </editor-fold>

# <editor-fold desc="JumpTo"?


def test_jumpto_dataset_id(session: SessionBase, new_dataset: Dataset):
    param_dataset_id = new_dataset.id
    param_latest_dataset_version = mc.get_latest_dataset_version(param_dataset_id)
    param_latest_dataset_version_id = param_latest_dataset_version.id

    returned_latest_dataset_version_id = mc.get_dataset_version_id_from_any(
        param_dataset_id
    )

    assert param_latest_dataset_version_id == returned_latest_dataset_version_id


def test_jumpto_dataset_version_id(session: SessionBase, new_dataset: Dataset):
    param_latest_dataset_version = mc.get_latest_dataset_version(new_dataset.id)
    param_latest_dataset_version_id = param_latest_dataset_version.id

    returned_latest_dataset_version_id = mc.get_dataset_version_id_from_any(
        param_latest_dataset_version_id
    )

    assert param_latest_dataset_version_id == returned_latest_dataset_version_id


@pytest.mark.parametrize("dataset_identifier", ["id", "permaname"])
@pytest.mark.parametrize("separator", [".", "/"])
def test_jumpto_dataset_id_with_separator_version_latest(
    session: SessionBase,
    new_dataset: Dataset,
    new_upload_session_file,
    separator: str,
    dataset_identifier: str,
):
    param_dataset_version = add_version(
        dataset=new_dataset, new_upload_session_file=new_upload_session_file
    )
    param_latest_dataset_version_id = param_dataset_version.id
    identifier_and_version = (
        getattr(new_dataset, dataset_identifier)
        + separator
        + str(param_dataset_version.version)
    )

    returned_latest_dataset_version_id = mc.get_dataset_version_id_from_any(
        identifier_and_version
    )

    assert param_latest_dataset_version_id == returned_latest_dataset_version_id


@pytest.mark.parametrize("dataset_identifier", ["id", "permaname"])
@pytest.mark.parametrize("separator", [".", "/"])
def test_jumpto_dataset_id_with_separator_version_first(
    session: SessionBase,
    new_dataset: Dataset,
    new_upload_session_file,
    separator: str,
    dataset_identifier: str,
):
    # Adding a dataset_version to check we return the first one and not the last one
    add_version(dataset=new_dataset, new_upload_session_file=new_upload_session_file)

    param_first_dataset_version = new_dataset.dataset_versions[0]
    param_first_dataset_version_id = param_first_dataset_version.id
    identifier_and_version = (
        getattr(new_dataset, dataset_identifier)
        + separator
        + str(param_first_dataset_version.version)
    )

    returned_first_dataset_version_id = mc.get_dataset_version_id_from_any(
        identifier_and_version
    )

    assert param_first_dataset_version_id == returned_first_dataset_version_id


# </editor-fold

# <editor-fold desc="Test Virtual datasets">
def test_basic_create_virtual_dataset(session: SessionBase):
    # create mock data of a single dataset and a virtual dataset which references the files but with a different name
    _new_datafile = mc.add_s3_datafile(
        name="underlying-datafile",
        s3_bucket="broadtaiga2prototype",
        s3_key=mc.generate_convert_key(),
        type=mc.S3DataFile.DataFileFormat.Raw,
        short_summary="short",
        long_summary="long",
    )

    mc.add_dataset(
        name="underlying-dataset", description="", datafiles_ids=[_new_datafile.id]
    )

    virtual_datafile = mc.add_virtual_datafile(
        name="alias", datafile_id=_new_datafile.id
    )

    virtual_dataset = mc.add_dataset(
        name="virtual-dataset", description="desc", datafiles_ids=[virtual_datafile.id]
    )

    # make sure the subsequent queries can find new objects
    session.flush()

    assert virtual_dataset.id is not None

    v = mc.get_dataset(virtual_dataset.id)
    assert v.name == "virtual-dataset"

    assert len(v.dataset_versions) == 1

    version = v.dataset_versions[0]
    assert len(version.datafiles)

    entry = version.datafiles[0]
    assert entry.name == "alias"
    assert entry.underlying_data_file.id == _new_datafile.id


# </editor-fold
