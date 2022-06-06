from datetime import datetime
import enum
from random import randint
import flask
from flask import current_app
import uuid
import os
import re

from typing import List, Dict, Tuple, Optional

import json

from sqlalchemy import and_, update, insert, exc

import taiga2.models as models
from taiga2.models import ReadAccessLog, db
from taiga2.third_party_clients import aws
from taiga2.models import (
    User,
    Folder,
    Dataset,
    DatasetPermaname,
    DataFile,
    S3DataFile,
    DatasetVersion,
    Entry,
    Group,
    VirtualDataFile,
    GCSObjectDataFile,
    Activity,
    CreationActivity,
    NameUpdateActivity,
    DescriptionUpdateActivity,
    FigshareDatasetVersionLink,
    FigshareDataFileLink,
    DatasetSubscription,
)
from taiga2.models import UploadSession, UploadSessionFile, ConversionCache
from taiga2.models import UserLog
from taiga2.models import ProvenanceGraph, ProvenanceNode, ProvenanceEdge
from taiga2.models import Group, EntryRightsEnum, resolve_virtual_datafile
from taiga2.models import SearchEntry, Breadcrumb

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm.session import make_transient
from collections import namedtuple
from connexion.exceptions import ProblemException
from taiga2.third_party_clients.gcs import get_blob, parse_gcs_path

DataFileAlias = namedtuple("DataFileAlias", "name data_file_id")

import logging

log = logging.getLogger(__name__)


# IMPORTANT:
#   If you have this error "RuntimeError: application not registered on db instance and
#   no application bound to current context" while trying around within command line,
#   You need to push the context of you app => app.app_context().push() (for us frontend_app.app_context().push()

# <editor-fold desc="User">


def api_error(msg):
    raise ProblemException(detail=msg)


def add_user(name, email, token=None):
    new_user = User(name=name, email=email, token=token)

    home_description = """Welcome to Taiga2: a light-weight repository for capturing, versioning and accessing datasets.

Make yourself comfortable, you're at Home."""

    home_folder = Folder(
        name="Home",
        description=home_description,
        folder_type=models.Folder.FolderType.home,
        creator=new_user,
    )

    trash_folder = Folder(
        name="Trash", folder_type=Folder.FolderType.trash, creator=new_user
    )

    db.session.add(home_folder)
    db.session.add(trash_folder)
    db.session.add(new_user)

    db.session.commit()

    # TODO: Find a fix to the home_folder and trash_folder issue
    new_user.home_folder = home_folder
    new_user.trash_folder = trash_folder

    db.session.commit()

    return new_user


def _get_test_user():
    return db.session.query(User).first()


def get_user(user_id):
    return db.session.query(User).filter(User.id == user_id).one()


def get_current_session_user() -> User:
    return flask.g.current_user


def get_user_by_name(user_name):
    return db.session.query(User).filter(User.name == user_name).one()


def get_user_by_email(user_email):
    return db.session.query(User).filter(User.email == user_email).one()


def get_user_by_token(user_token):
    q = db.session.query(User).filter(User.token == user_token)
    user = _fetch_respecting_one_or_none(q, one_or_none=True)
    return user


def get_all_users():
    users = db.session.query(User).all()
    return users


def _change_connected_user(new_user):
    """Allows to change the connected user. Mainly for testing purpose"""
    if new_user:
        flask.g.current_user = new_user
        return True
    else:
        return False


# </editor-fold>

# <editor-fold desc="Folder">
def add_folder(name, folder_type, description):
    creator = get_current_session_user()

    new_folder = Folder(
        name=name, folder_type=folder_type, description=description, creator=creator
    )
    db.session.add(new_folder)
    db.session.commit()

    return new_folder


def get_folder(folder_id, one_or_none=False) -> Folder:
    query = db.session.query(Folder).filter(Folder.id == folder_id)

    folder_or_none = _fetch_respecting_one_or_none(q=query, one_or_none=one_or_none)

    return folder_or_none


def get_rights(entry_id) -> EntryRightsEnum:
    entry = db.session.query(Entry).filter(Entry.id == entry_id).one()
    # We check the rights of this user over this folder
    current_user = get_current_session_user()

    admin_group = db.session.query(Group).filter(Group.name == "Admin").one()
    # If the user is the owner or it is in the group of admins, allowed to edit
    if entry.creator_id == current_user.id or current_user in admin_group.users:
        return EntryRightsEnum.can_edit
    else:
        return EntryRightsEnum.can_view


def get_folder_by_name(folder_name):
    """Get the folder by name of the current_user in the session. If multiple folders with the same name exist,
    returns the first one"""
    current_user = get_current_session_user()
    folder = (
        db.session.query(Folder)
        .filter(Folder.creator_id == current_user.id)
        .filter(Folder.name == folder_name)
        .first()
    )

    if folder is None:
        raise NoResultFound
    else:
        return folder


def get_public_folder():
    public_folder = db.session.query(Folder).filter(Folder.id == "public").first()
    return public_folder


def update_folder_name(folder_id, new_name) -> Folder:
    folder = get_folder(folder_id)

    folder.name = new_name
    db.session.add(folder)
    db.session.commit()

    return folder


def update_folder_description(folder_id, new_description) -> Folder:
    folder = get_folder(folder_id)

    folder.description = new_description
    db.session.add(folder)
    db.session.commit()

    return folder


def add_folder_entry(folder_id, entry_id):
    folder = get_folder(folder_id)
    entry = get_entry(entry_id)

    # TODO: See if this is the right place to do that...
    # TODO: Deactivate after the discussion with Phil. Only access to dataset for now
    # If it is a dataset, we need to update the location of its dataset_versions
    # if type(entry) is Dataset:
    # Add this folder to the dataset_versions
    # for dataset_version in entry.dataset_versions:
    #     add_folder_entry(folder_id, dataset_version.id)

    # TODO: This should be a set, not a list.
    if entry not in folder.entries:
        folder.entries.append(entry)

    db.session.add(folder)
    db.session.commit()

    return folder


def remove_folder_entry(folder_id, entry_id):
    folder = get_folder(folder_id)
    entry = get_entry(entry_id)

    folder.entries.remove(entry)

    db.session.add(folder)
    db.session.commit()

    return folder


# TODO: Populate this function?
def get_folders_containing():
    raise NotImplementedError


def get_parent_folders(entry_id):
    entry = db.session.query(Entry).filter(Entry.id == entry_id).one()
    parent_folders = entry.parents

    return parent_folders


# </editor-fold>

# <editor-fold desc="Dataset">
def add_dataset(
    name, description, datafiles_ids=None, permaname=None, anterior_creation_date=None
):
    # assert len(datafiles_ids) > 0

    if not permaname:
        permaname = models.generate_permaname(name)

    creator = get_current_session_user()

    creation_date = None
    if anterior_creation_date:
        creation_date = anterior_creation_date

    new_dataset = Dataset(name=name, creator=creator, creation_date=creation_date)

    db.session.add(new_dataset)
    db.session.flush()

    new_permaname_record = DatasetPermaname(
        permaname=permaname, dataset_id=new_dataset.id
    )
    db.session.add(new_permaname_record)

    # It means we would want to create a first dataset with a DatasetVersion
    # containing DataFiles

    # TODO: Think about a meaningful name
    if datafiles_ids is not None:
        db.session.flush()
        new_dataset_version = add_dataset_version(
            dataset_id=new_dataset.id,
            datafiles_ids=datafiles_ids,
            new_description=description,
            anterior_creation_date=creation_date,
        )

        db.session.add(new_dataset_version)

    db.session.commit()

    # Add the related activity
    # TODO: Add the activity
    # TODO: Think about an automatic way of adding/updating the activity
    return new_dataset


def add_dataset_from_session(
    session_id, dataset_name, dataset_description, current_folder_id
):
    current_user = get_current_session_user()

    added_datafiles = add_datafiles_from_session(session_id)

    # TODO: Get the user from the session
    user = get_user_from_upload_session(session_id)
    dataset_permaname = models.generate_permaname(dataset_name)
    added_dataset = add_dataset(
        name=dataset_name,
        permaname=dataset_permaname,
        description=dataset_description,
        datafiles_ids=[datafile.id for datafile in added_datafiles],
    )
    add_folder_entry(current_folder_id, added_dataset.id)

    activity = CreationActivity(
        user_id=current_user.id,
        dataset_id=added_dataset.id,
        type=Activity.ActivityType.created,
        dataset_name=dataset_name,
        dataset_description=dataset_description,
    )
    db.session.add(activity)
    db.session.commit()

    add_dataset_subscription(added_dataset.id)

    return added_dataset


def update_permaname(dataset_id, permaname):
    permaname_record = DatasetPermaname(permaname=permaname, dataset_id=dataset_id)
    db.session.add(permaname_record)
    db.session.commit()


def get_dataset(dataset_id, one_or_none=False) -> Dataset:
    q = db.session.query(Entry).filter(Entry.id == dataset_id)
    return _fetch_respecting_one_or_none(q, one_or_none, expect=[Dataset])


def get_datasets(array_dataset_ids):
    return [get_dataset(id) for id in array_dataset_ids]


def get_dataset_from_permaname(dataset_permaname, one_or_none=False):
    dataset = (
        db.session.query(Dataset)
        .filter(Dataset.permanames.any(DatasetPermaname.permaname == dataset_permaname))
        .one_or_none()
    )

    if not one_or_none and dataset is None:
        raise NoResultFound()

    return dataset


def get_first_dataset_version(dataset_id):
    dataset_version_first = (
        db.session.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.version == 1)
        .one()
    )

    return dataset_version_first


def get_dataset_version_by_dataset_id_and_version(dataset_id, version_number):
    dataset_version = (
        db.session.query(DatasetVersion)
        .filter(
            DatasetVersion.dataset_id == dataset_id,
            DatasetVersion.version == version_number,
        )
        .one()
    )

    return dataset_version


def get_latest_dataset_version(dataset_id):
    dataset = get_dataset(dataset_id)
    max_version = 0
    dataset_version_latest_version = None
    for dataset_version in dataset.dataset_versions:
        if dataset_version.version > max_version:
            dataset_version_latest_version = dataset_version
            max_version = dataset_version.version

    return dataset_version_latest_version


def update_dataset_name(dataset_id, name) -> Dataset:
    current_user = get_current_session_user()

    dataset = get_dataset(dataset_id)

    dataset.name = name
    # TODO: Update the permaname with the new name
    new_permaname = models.generate_permaname(name)
    new_permaname_record = DatasetPermaname(
        permaname=new_permaname, dataset_id=dataset.id
    )
    db.session.add(dataset)
    db.session.add(new_permaname_record)

    activity = NameUpdateActivity(
        user_id=current_user.id,
        dataset_id=dataset.id,
        type=Activity.ActivityType.changed_name,
        dataset_name=name,
    )
    db.session.add(activity)

    db.session.commit()

    return dataset


def update_dataset_creation_date(dataset_id, new_date):
    """Update the creation date of a dataset. The format of the string new_date should be: %Y-%m-%d %H:%M:%S.%f
    (see https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior)"""
    dataset = get_entry(dataset_id)

    dataset.creation_date = _get_datetime_from_string(new_date)

    db.session.add(dataset)
    db.session.commit()


# TODO: update_datafile_summaries
# def update_datafile_summaries


def update_dataset_contents(
    dataset_id,
    datafiles_id_to_remove=None,
    datafiles_id_to_add=None,
    new_description=None,
    comments="No comments",
):
    # TODO: Does it make sense to have a "add datafiles?". Each datafile belongs to a dataset_version
    if not datafiles_id_to_remove:
        datafiles_id_to_remove = []
    if not datafiles_id_to_add:
        datafiles_id_to_add = []

    # Fetch the entries to remove
    datafiles_to_remove = [
        get_datafile(datafile_id_to_remove)
        for datafile_id_to_remove in datafiles_id_to_remove
    ]

    # Fetch the entries to add
    datafiles_to_add = [
        get_datafile(datafile_id_to_add) for datafile_id_to_add in datafiles_id_to_add
    ]

    dataset = get_dataset(dataset_id)

    # Fetch the last version
    # TODO: Make a function to retrieve the last version
    # TODO: Improve this using db.session.query => OperationalError currently
    max_version = 0
    dataset_version_latest_version = None
    for dataset_version in dataset.dataset_versions:
        if dataset_version.version > max_version:
            dataset_version_latest_version = dataset_version

    # latest_version_datafiles = dataset_version_latest_version.datafiles

    # Create the new dataset_version from the latest and update its version
    # TODO: Remove the increment of the version since it should be handled by add_dataset_version directly
    new_updated_dataset_version = add_dataset_version(
        dataset_id=dataset_version_latest_version.dataset.id,
        datafiles_ids=[
            datafile.id for datafile in dataset_version_latest_version.datafiles
        ],
        new_description=new_description,
    )

    new_updated_version_datafiles = new_updated_dataset_version.datafiles

    # dataset_version_latest_version = dataset.dataset_versions
    # dataset_version_latest_version = db.session.query(DatasetVersion, Dataset) \
    #                                             .filter(Dataset.id == dataset_id) \
    #                                             .order_by(DatasetVersion.version) \
    #                                             .first()

    # TODO: Inefficient, but for now it maybe does not matter because datafiles is not big
    # Remove the datafiles
    for datafile_to_remove in datafiles_to_remove:
        if datafile_to_remove in new_updated_version_datafiles:
            new_updated_version_datafiles.remove(datafile_to_remove)

    # Add the datafiles
    for datafile_to_add in datafiles_to_add:
        if datafiles_to_add not in new_updated_version_datafiles:
            new_updated_version_datafiles.append(datafile_to_add)

    db.session.add(new_updated_dataset_version)
    db.session.commit()

    return dataset


def delete_dataset(dataset_id):
    # Remove the dataset
    ds = get_dataset(dataset_id=dataset_id)

    db.session.delete(ds)
    db.session.commit()
    # Clean up
    # TODO: Shouldn't have to clean up, see Cascade and co


def add_or_update_dataset_access_log(dataset_id) -> UserLog:
    """Create or update, with the current datetime, the access log for the current user, on the dataset
    passed in parameter"""

    current_user = flask.g.current_user

    try:
        access_log = (
            db.session.query(UserLog)
            .filter(UserLog.dataset_id == dataset_id)
            .filter(UserLog.user_id == current_user.id)
            .one_or_none()
        )
    except MultipleResultsFound:
        log.error(
            "When logging access to dataset (id {}) for user {}, we had multiple results instead of only one".format(
                dataset_id, current_user.email
            )
        )

    if access_log:
        access_log.last_access = datetime.utcnow()
    else:
        access_log = UserLog(user_id=current_user.id, dataset_id=dataset_id)

    db.session.add(access_log)
    db.session.commit()

    return access_log


def get_datasets_access_logs():
    current_user = flask.g.current_user

    array_access_logs = (
        db.session.query(UserLog).filter(UserLog.user_id == current_user.id).all()
    )

    return array_access_logs


def get_dataset_version_id_from_any(submitted_by_user__data: str):
    """
    Try to retrieve the dataset version id from a user entered string.
    Can be of form:
    - dataset_id
    - dataset_id.version
    - dataset_id/version
    - dataset_permaname
    - dataset_permaname.version
    - dataset_permaname/version
    - dataset_version_id

    Raise NotFound exception if dataset_id nor dataset_version_id matches something existing
    """
    # TODO: Do a function to extract this pattern . and /
    version = None
    if "." in submitted_by_user__data:
        dataset_id, version = submitted_by_user__data.split(".")
    elif "/" in submitted_by_user__data:
        dataset_id, version = submitted_by_user__data.split("/")
    else:
        # TODO: implement dataset_id or dataset_version_id
        dataset_id = submitted_by_user__data

    dataset = get_dataset(dataset_id, one_or_none=True)

    # If no result from dataset, trying dataset_version
    if not dataset:
        # Try permaname, and if still doesn't work, maybe it is a dataset_version_id
        dataset = get_dataset_from_permaname(dataset_id, one_or_none=True)

        if not dataset:
            # TODO: It seems weird, but user could enter the dataset version id in the jump box. We have to confirm it is the right id
            dataset_version_id = dataset_id
            dataset_version = get_dataset_version(
                dataset_version_id=dataset_version_id, one_or_none=True
            )

    if dataset:
        if not version:
            dataset_version = get_latest_dataset_version(dataset.id)
        else:
            dataset_version = get_dataset_version_by_permaname_and_version(
                dataset.permaname, version, one_or_none=True
            )

    # We did not find anything matching
    if not dataset_version:
        return None

    return dataset_version.id


# </editor-fold>

# <editor-fold desc="DatasetVersion">
def _add_dataset_version(
    dataset_id,
    datafiles_ids=None,
    new_description=None,
    changes_description=None,
    permaname=None,
    anterior_creation_date=None,
    forced_id=None,
):
    assert len(datafiles_ids) > 0
    assert isinstance(datafiles_ids, list)

    # Fetch the object from the database
    creator = get_current_session_user()

    dataset = get_entry(dataset_id)

    datafiles = db.session.query(DataFile).filter(DataFile.id.in_(datafiles_ids)).all()

    assert len(datafiles) == len(datafiles_ids)

    latest_dataset_version = get_latest_dataset_version(dataset_id)
    if latest_dataset_version:
        version = latest_dataset_version.version + 1
    else:
        version = 1

    # If we did not set a name for the dataset_version, we take one by default
    name = str(version)

    creation_date = None
    if anterior_creation_date:
        creation_date = _get_datetime_from_string(anterior_creation_date)

    # Create the DatasetVersion object
    new_dataset_version = DatasetVersion(
        name=name,
        creator=creator,
        dataset=dataset,
        datafiles=datafiles,
        description=new_description,
        changes_description=changes_description,
        version=version,
        creation_date=creation_date,
        id=forced_id,
    )

    db.session.add(new_dataset_version)
    db.session.add(dataset)

    return new_dataset_version


def add_dataset_version(
    dataset_id,
    datafiles_ids=None,
    new_description=None,
    changes_description=None,
    permaname=None,
    anterior_creation_date=None,
    forced_id=None,
):
    new_dataset_version = _add_dataset_version(
        dataset_id,
        datafiles_ids,
        new_description,
        changes_description,
        permaname,
        anterior_creation_date,
        forced_id,
    )
    db.session.commit()

    return new_dataset_version


def _datafiles_equivalent(datafile, other_datafile):
    datafile_id = resolve_virtual_datafile(datafile).id
    other_datafile_id = resolve_virtual_datafile(other_datafile).id
    return datafile_id == other_datafile_id


def get_dataset_version_datafiles_diff(new_datafiles, previous_datafiles):
    datafile_diff = {"updated": [], "added": [], "removed": [], "renamed": []}

    for datafile in new_datafiles:
        previous_datafile = next(
            (
                previous_datafile
                for previous_datafile in previous_datafiles
                if previous_datafile.name == datafile.name
            ),
            None,
        )
        if previous_datafile:
            previous_datafiles.remove(previous_datafile)
            if not _datafiles_equivalent(datafile, previous_datafile):
                datafile_diff["updated"].append(datafile)
            continue

        previous_datafile = next(
            (
                previous_datafile
                for previous_datafile in previous_datafiles
                if _datafiles_equivalent(datafile, previous_datafile)
            ),
            None,
        )
        if previous_datafile:
            previous_datafiles.remove(previous_datafile)
            datafile_diff["renamed"].append((datafile, previous_datafile))
            continue

        datafile_diff["added"].append(datafile)

    datafile_diff["removed"] = previous_datafiles

    return datafile_diff


def format_datafile_diff(datafile_diff):
    def format_added_removed_updated(datafiles):
        return ["- {}".format(datafile.name) for datafile in datafiles]

    def format_renamed(datafiles):
        return [
            "- {} -> {}".format(previous_datafile.name, datafile.name)
            for (datafile, previous_datafile) in datafiles
        ]

    comments = ""
    for category in ["added", "removed", "updated", "renamed"]:
        if len(datafile_diff[category]):
            if comments != "":
                comments += "\n"

            comments += "{}:\n".format(category.capitalize())
            f = (
                format_added_removed_updated
                if category in ["added", "removed", "updated"]
                else format_renamed
            )
            comments += "\n".join(f(datafile_diff[category]))
    return comments


def filter_allowed_parents(parents):
    allowed_parents = parents

    for index, folder in enumerate(parents):
        if not can_view(folder.id):
            del allowed_parents[index]

    return allowed_parents


def get_previous_version_and_added_datafiles(
    dataset_version: DatasetVersion, dataset_id: str
) -> List[DataFile]:
    version = None
    if dataset_version is None:
        version = get_latest_dataset_version(dataset_id)
    else:
        assert dataset_version.version is not None
        version = get_dataset_version_by_dataset_id_and_version(
            dataset_id, dataset_version.version
        )

    return version.datafiles


def lock():
    # We implement a lock by relying on the database to block clients which attempt to
    # update the same row. Once the transaction which successfully updates this row is
    # either committed or rolled back the "lock" will be released
    random_val = randint(1, 9999)
    db.session.execute("UPDATE lock_table SET random = :val", {"val": random_val})


def add_version_addition_activity(activity):
    db.session.add(activity)
    db.session.commit()


def _fetch_respecting_one_or_none(q, one_or_none, expect=None):
    """If one_or_none is set, asks the query q to return none if NoResultFound, else raise the error"""
    if one_or_none:
        obj = q.one_or_none()
        if obj is None:
            return None
    else:
        obj = q.one()

    if expect is not None:
        for expected_class in expect:
            if isinstance(obj, expected_class):
                return obj
        print("Expected {} (type={}) to be one of {}".format(obj, type(obj), expect))
        # simulate the behavior of asking for the wrong type, would report no such record
        if one_or_none:
            return None
        else:
            raise NoResultFound()
    else:
        return obj


def get_dataset_version(dataset_version_id, one_or_none=False) -> DatasetVersion:

    q = db.session.query(Entry).filter(Entry.id == dataset_version_id)

    return _fetch_respecting_one_or_none(q, one_or_none, expect=[DatasetVersion])


def get_dataset_versions_bulk(array_dataset_version_ids):
    dataset_versions = (
        db.session.query(DatasetVersion)
        .filter(DatasetVersion.id.in_(array_dataset_version_ids))
        .all()
    )

    return dataset_versions


def get_dataset_version_provenance(dataset_version_id, provenance):
    # TODO: See how to manage the provenance
    raise NotImplementedError


def get_latest_dataset_version_by_permaname(permaname):
    dataset_version = (
        db.session.query(models.DatasetVersion)
        .filter(
            DatasetVersion.dataset.has(
                Dataset.permanames.any(DatasetPermaname.permaname == permaname)
            )
        )
        .order_by(DatasetVersion.version.desc())
        .first()
    )

    return dataset_version


def get_dataset_version_by_permaname_and_version(permaname, version, one_or_none=False):
    """From the permaname of a dataset, retrieve the specific dataset version"""
    # dataset = get_dataset_from_permaname(permaname)
    obj = (
        db.session.query(DatasetVersion)
        .filter(DatasetVersion.version == version)
        .filter(
            DatasetVersion.dataset.has(
                Dataset.permanames.any(DatasetPermaname.permaname == permaname)
            )
        )
        .one_or_none()
    )

    if not one_or_none and obj is None:
        raise NoResultFound()
    # assert obj is not None, "Could not find permaname {}, version {}".format(permaname, version)

    return obj


def get_dataset_version_by_dataset_id_and_dataset_version_id(
    dataset_id, dataset_version_id, one_or_none=False
):
    dataset_version = get_dataset_version(dataset_version_id, one_or_none=one_or_none)

    return dataset_version


def update_dataset_version_description(dataset_version_id, new_description):
    current_user = get_current_session_user()

    dataset_version = get_dataset_version(dataset_version_id)

    dataset_version.description = new_description

    activity = DescriptionUpdateActivity(
        user_id=current_user.id,
        dataset_id=dataset_version.dataset_id,
        type=Activity.ActivityType.changed_description,
        dataset_description=new_description,
        dataset_version=dataset_version.version,
    )

    db.session.add(dataset_version)
    db.session.add(activity)
    db.session.commit()

    return dataset_version


def change_dataset_version_state(
    dataset_version_id: str,
    datasetVersionState: DatasetVersion.DatasetVersionState,
    reason: str = None,
) -> DatasetVersion:
    """Function to change the state of a DatasetVersion
    :param dataset_version_id:
    :param datasetVersionState:
    :param reason:
    :return:
    """
    # TODO: Could live in models.py as a method of a DatasetVersion
    dataset_version = get_dataset_version(dataset_version_id)

    dataset_version.state = datasetVersionState

    # We don't touch reason if it is not set (to keep deprecation state in deletion => deprecation workflow)
    if reason:
        dataset_version.reason_state = reason

    db.session.add(dataset_version)
    db.session.commit()

    return dataset_version


def deprecate_dataset_version(
    dataset_version_id: str, reason: str
) -> DatasetVersion.DatasetVersionState:
    """Change the current state of a DatasetVersion to deprecate (see DatasetVersionState)
    :param dataset_version_id: ID of the dataset version to deprecate
    :param reason: Reason for deprecating a dataset
    :return: The new DatasetVersionState (should be deprecated)
    """
    dataset_version = get_dataset_version(dataset_version_id=dataset_version_id)

    if dataset_version.state == DatasetVersion.DatasetVersionState.deleted:
        # TODO: We could do better here, since deprecate_dataset_version_from_delete_state is now only internally used
        deprecate_dataset_version_from_delete_state(dataset_version_id)
    elif dataset_version.state == DatasetVersion.DatasetVersionState.approved:
        # Check reason is not empty
        assert reason, "Reason can't be empty when deprecating a dataset version"

        dataset_version = change_dataset_version_state(
            dataset_version_id=dataset_version_id,
            datasetVersionState=DatasetVersion.DatasetVersionState.deprecated,
            reason=reason,
        )
    return dataset_version.state


def deprecate_dataset_version_from_delete_state(
    dataset_version_id: str,
) -> DatasetVersion.DatasetVersionState:
    """
    This function is mainly here to retrieve the reason message of deprecation (so if deletion was a mistake,
    we have nothing specific to do
    :param dataset_version_id:
    :return: The new DatasetVersionState (should be deprecated)
    """
    dataset_version = get_dataset_version(dataset_version_id=dataset_version_id)

    dataset_version = change_dataset_version_state(
        dataset_version_id=dataset_version_id,
        datasetVersionState=DatasetVersion.DatasetVersionState.deprecated,
        reason=dataset_version.reason_state,
    )

    return dataset_version.state


def approve_dataset_version(
    dataset_version_id: str,
) -> DatasetVersion.DatasetVersionState:
    """Change the current state of a DatasetVersion to approve (see DatasetVersionState).
    It should be the state by default
    :param dataset_version_id: ID of the dataset version to approve
    :return The new DatasetVersionState (should be approved)
    """
    dataset_version = change_dataset_version_state(
        dataset_version_id=dataset_version_id,
        datasetVersionState=DatasetVersion.DatasetVersionState.approved,
    )

    return dataset_version.state


def delete_dataset_version(
    dataset_version_id: str,
) -> DatasetVersion.DatasetVersionState:
    """Change the current state of a DatasetVersion to deleted (see DatasetVersionState).
    :param dataset_version_id: ID of the dataset version to delete
    :return The new DatasetVersionState (should be deleted)
    """
    dataset_version = change_dataset_version_state(
        dataset_version_id=dataset_version_id,
        datasetVersionState=DatasetVersion.DatasetVersionState.deleted,
    )

    return dataset_version.state


# </editor-fold>

# <editor-fold desc="Entry">
def get_entry(entry_id):
    entry = db.session.query(Entry).filter(Entry.id == entry_id).one()

    return entry


class EntryAction(enum.Enum):
    move = 1
    copy = 2


def _action_to_folder(
    entry_ids, target_folder_id, entry_action, current_folder_id=None
):
    if current_folder_id:
        folder_from_action = get_entry(current_folder_id)
    folder_to_action = get_entry(target_folder_id)

    for entry_id in entry_ids:
        entry = get_entry(entry_id)
        # If the requested action is EntryAction.move => We replace the current parent to the target one
        if entry_action == EntryAction.move:
            # entry.parents = [folder_to_action]
            # TODO: Catch the exception for ValueError

            # If we don't have a current_folder, then we don't remove it, but we log there is something strange
            if current_folder_id is None:
                # TODO: Reactivate this when migration is done
                # log.warn("The move action for the entry {} did not receive a current folder id as parameter. "
                #          "Just adding to the target folder {} (id {}).".format(entry_ids, folder_to_action,
                #                                                                folder_to_action.id))
                pass
            else:
                entry.parents.remove(folder_from_action)

            if folder_to_action not in entry.parents:
                entry.parents.append(folder_to_action)

            db.session.add(entry)
        # If the requested action is EntryAction.copy:
        # We create a new dataset, and we populate it with the datasetVersions and the datafiles
        elif entry_action == EntryAction.copy:
            # TODO: Think about changing the parents to a set instead of a simple array
            if folder_to_action not in entry.parents:
                entry.parents.append(folder_to_action)

            db.session.add(entry)

    db.session.commit()


def move_to_trash(entry_ids):
    """Remove the parents folder, and add the user Trash folder as the only parent folder
    Input: Array of entry ids
    """
    # Get the current user's trash folder
    current_user = get_current_session_user()
    trash_folder = current_user.trash_folder

    _action_to_folder(
        entry_ids=entry_ids, folder_id=trash_folder.id, entry_action=EntryAction.move
    )


def move_to_folder(entry_ids, current_folder_id, target_folder_id):
    # If we don't get a target_folder_id, it means we want to put it into the trash
    if not target_folder_id:
        # Get the current user's trash folder
        current_user = get_current_session_user()
        trash_folder = current_user.trash_folder

        target_folder_id = trash_folder.id

    # TODO: Check if the user is allowed to do this?
    _action_to_folder(
        entry_ids=entry_ids,
        current_folder_id=current_folder_id,
        target_folder_id=target_folder_id,
        entry_action=EntryAction.move,
    )


def copy_to_folder(entry_ids, target_folder_id):
    _action_to_folder(
        entry_ids=entry_ids,
        target_folder_id=target_folder_id,
        entry_action=EntryAction.copy,
    )


def changer_owner(entry_id, new_creator_id):
    entry = get_entry(entry_id)
    entry.creator_id = new_creator_id

    db.session.add(entry)
    db.session.commit()


def already_seen(entry_id):
    """Return True if the current user has already seen the entry"""
    visited_list = (
        db.session.query(UserLog)
        .filter(UserLog.entry_id == entry_id)
        .filter(UserLog.user == get_current_session_user())
        .all()
    )

    if visited_list:
        return True
    else:
        return False


def can_view(entry_id):
    """Return True if the current user can view the entry"""
    entry = get_entry(entry_id=entry_id)

    current_user = get_current_session_user()

    public_folder = get_entry("public")

    # If we are the owner of the entry, we can view it
    if entry.creator == current_user:
        return True
    # If the current_user has already seen this entry, via its access log, we can view it
    elif already_seen(entry_id):
        return True
    else:
        return False


# </editor-fold>

# <editor-fold desc="DataFile">
def _add_s3_datafile(
    s3_bucket,
    s3_key,
    compressed_s3_key: Optional[str],
    name,
    type,
    encoding,
    short_summary,
    long_summary,
    column_types=None,
    original_file_sha256=None,
    original_file_md5=None,
    forced_id=None,
):
    assert type is not None
    received_type = type
    # TODO: See register_datafile_id
    new_datafile_name = name
    # We try to manage properly the type
    if not isinstance(received_type, models.S3DataFile.DataFileFormat):
        for data_file_type in models.S3DataFile.DataFileFormat:
            if str.lower(data_file_type.value) == str.lower(type):
                received_type = data_file_type

    if not isinstance(received_type, models.S3DataFile.DataFileFormat):
        message = "The type does not match an allowed one"
        log.error(message)
        raise Exception(message)

    new_datafile = S3DataFile(
        name=new_datafile_name,
        s3_bucket=s3_bucket,
        s3_key=s3_key,
        compressed_s3_key=compressed_s3_key,
        format=received_type,
        encoding=encoding,
        short_summary=short_summary,
        long_summary=long_summary,
        column_types_as_json=column_types,
        id=forced_id,
        original_file_sha256=original_file_sha256,
        original_file_md5=original_file_md5,
    )

    db.session.add(new_datafile)
    db.session.flush()

    return new_datafile


def add_s3_datafile(
    s3_bucket,
    s3_key,
    compressed_s3_key: Optional[str],
    name,
    type,
    encoding,
    short_summary,
    long_summary,
    column_types=None,
    original_file_sha256=None,
    original_file_md5=None,
    forced_id=None,
):
    new_datafile = _add_s3_datafile(
        s3_bucket=s3_bucket,
        s3_key=s3_key,
        compressed_s3_key=compressed_s3_key,
        name=name,
        type=type,
        encoding=encoding,
        short_summary=short_summary,
        long_summary=long_summary,
        column_types=column_types,
        original_file_sha256=original_file_sha256,
        original_file_md5=original_file_md5,
        forced_id=forced_id,
    )

    db.session.commit()

    return new_datafile


def _add_virtual_datafile(name, datafile_id):
    assert isinstance(datafile_id, str)

    datafile = DataFile.query.get(datafile_id)
    assert datafile is not None

    new_datafile = VirtualDataFile(name=name, underlying_data_file=datafile)

    db.session.add(new_datafile)

    db.session.flush()

    # some sanity checks to make sure persistence worked as expected
    _id = new_datafile.id
    db.session.expunge(new_datafile)
    new_datafile_2 = VirtualDataFile.query.get(_id)
    assert id(new_datafile) != id(new_datafile_2)
    new_datafile = new_datafile_2
    assert new_datafile.id is not None
    assert new_datafile.underlying_data_file.id is not None
    assert new_datafile.underlying_data_file_id is not None

    return new_datafile


def add_virtual_datafile(name, datafile_id):
    new_datafile = _add_virtual_datafile(name=name, datafile_id=datafile_id)
    db.session.commit()

    return new_datafile


def _add_gcs_datafile(name, gcs_path, generation_id):
    new_datafile = GCSObjectDataFile(
        name=name, gcs_path=gcs_path, generation_id=generation_id
    )

    db.session.add(new_datafile)

    db.session.flush()

    return new_datafile


def add_gcs_datafile(name, gcs_path, generation_id):
    new_datafile = _add_gcs_datafile(
        name=name, gcs_path=gcs_path, generation_id=generation_id
    )

    db.session.commit()

    return new_datafile


# def add_virtual_datafile(name, datafile_id):
#     assert isinstance(datafile_id, str)
#
#     datafile = DataFile.query.get(datafile_id)
#     assert datafile is not None
#
#     # new_datafile = VirtualDataFile(name=name,
#     #                                underlying_data_file=datafile)
#     #
#     # db.session.add(new_datafile)
#     from taiga2.models import generate_uuid
#
#     id = generate_uuid()
#     db.session.execute(VirtualDataFile.__table__.insert(), dict(type='virtual', id=id, underlying_data_file_id=datafile_id, name=name))
#     print("****")
#     db.session.commit()
#
#     # _id = new_datafile.id
#     # db.session.expunge(new_datafile)
#     new_datafile = VirtualDataFile.query.get(id)
#     # assert id(new_datafile) != id(new_datafile_2)
#
#     # new_datafile = new_datafile_2
#     assert new_datafile.id is not None
#
#     assert new_datafile.underlying_data_file.id is not None
#
#     return new_datafile


def get_datafile_by_version_and_name(dataset_version_id, name, one_or_none=False):
    obj = (
        db.session.query(DataFile)
        .filter(DataFile.name == name)
        .filter(DataFile.dataset_version_id == dataset_version_id)
        .one_or_none()
    )

    if obj is None and not one_or_none:
        raise NoResultFound()

    return obj


def get_datafile(datafile_id) -> DataFile:
    datafile = db.session.query(DataFile).filter(DataFile.id == datafile_id).one()

    return datafile


class InvalidTaigaIdFormat(Exception):
    def __init__(self, taiga_id: str):
        self.taiga_id = taiga_id


def get_datafile_by_taiga_id(taiga_id: str, one_or_none=False) -> Optional[DataFile]:
    m = re.match("([a-z0-9-]+)\\.(\\d+)/(.*)", taiga_id)
    if m is None:
        raise InvalidTaigaIdFormat(taiga_id)
    permaname = m.group(1)
    version = m.group(2)
    filename = m.group(3)
    dataset_version = get_dataset_version_by_permaname_and_version(
        permaname, version, one_or_none=one_or_none
    )
    if dataset_version is None:
        return None

    datafile = get_datafile_by_version_and_name(
        dataset_version.id, filename, one_or_none=one_or_none
    )
    if datafile is None:
        return None

    return resolve_virtual_datafile(datafile)


def get_comments_and_latest_dataset_version(dataset_id, added_datafiles):
    latest_dataset_version = get_latest_dataset_version(dataset_id)

    datafile_diff = get_dataset_version_datafiles_diff(
        list(added_datafiles), list(latest_dataset_version.datafiles)
    )

    comments = format_datafile_diff(datafile_diff)

    return comments, latest_dataset_version


def get_session_files_including_existing_files(session_id, dataset_version, dataset_id):
    new_files = get_upload_session_files_from_session(session_id)
    previous_version_datafiles = get_previous_version_and_added_datafiles(
        dataset_version, dataset_id
    )

    datafile_names_to_exclude = [file.filename for file in new_files]

    # If a new file has the same name as a previous_version_file, overrite the previous_version_file
    previous_version_virtual_datafiles: List[DataFile] = []
    if previous_version_datafiles is not None:
        for upload_datafile in previous_version_datafiles:
            if upload_datafile.name not in datafile_names_to_exclude:
                previous_version_virtual_datafiles.append(upload_datafile)

    # Add upload session file for each previous datafile
    for file in previous_version_virtual_datafiles:
        add_upload_session_virtual_file(
            session_id=session_id,
            filename=file.name,
            data_file_id=file.id,
            commit=False,
        )

    # Get the all_datafiles, including previous data files. These can all now be retrieved from the session.
    all_datafiles = _add_datafiles_from_session(session_id)

    return all_datafiles


def log_datafile_read_access_info(datafile_id: str):
    # If the user has read this data file, a row with this datafiles access info will already exist, so update that
    # row's access count and last access time info. Otherwise, add a row to track the read access of this file for this user.
    user = get_current_session_user()
    user_id = user.id

    table = ReadAccessLog.__table__
    connection = db.engine.connect()

    with connection.begin():
        try:
            connection.execute("SAVEPOINT my_savepoint;")
            stmt = insert(table).values(
                datafile_id=datafile_id,
                user_id=user_id,
                first_access=datetime.utcnow(),
                last_access=datetime.utcnow(),
                access_count=1,
            )
            connection.execute(stmt)
        except exc.IntegrityError:
            connection.execute("ROLLBACK TO SAVEPOINT my_savepoint;")
            stmt = (
                update(table)
                .values(
                    last_access=datetime.utcnow(), access_count=table.c.access_count + 1
                )
                .where(
                    table.c.datafile_id == datafile_id and table.c.user_id == user_id
                )
            )
            connection.execute(stmt)

    db.session.commit()


def _add_datafiles_from_session(session_id: str):
    # We retrieve all the upload_session_files related to the UploadSession
    added_files = get_upload_session_files_from_session(session_id)

    # Generate the datafiles from these files
    added_datafiles = []
    for file in added_files:
        if file.data_file is not None:
            new_datafile = _add_virtual_datafile(
                name=file.filename, datafile_id=file.data_file.id
            )
        elif file.gcs_path is not None:
            new_datafile = _add_gcs_datafile(
                name=file.filename,
                gcs_path=file.gcs_path,
                generation_id=file.generation_id,
            )
        else:
            new_datafile = _add_s3_datafile(
                name=file.filename,
                s3_bucket=file.s3_bucket,
                s3_key=file.converted_s3_key,
                compressed_s3_key=file.compressed_s3_key,
                type=file.converted_filetype,
                encoding=file.encoding,
                short_summary=file.short_summary,
                long_summary=file.long_summary,
                column_types=file.column_types_as_json,
                original_file_sha256=file.original_file_sha256,
                original_file_md5=file.original_file_md5,
            )
        added_datafiles.append(new_datafile)

    return added_datafiles


def add_datafiles_from_session(session_id: str):
    added_datafiles = _add_datafiles_from_session(session_id)
    db.session.commit()

    return added_datafiles


def copy_datafile(original_datafile_id: str) -> DataFile:
    original_datafile = get_datafile(original_datafile_id)
    # Creates a new object that has only the attributes of this very table. No foreign keys.
    make_transient(original_datafile)
    # Just to make it clear this is a new object
    _copy_datafile = original_datafile
    # Db will assign a new id
    _copy_datafile.id = None

    # We also remove the link from the old dataset_version_id to prevent the unique constraint to trigger
    _copy_datafile.dataset_version = None

    db.session.add(_copy_datafile)
    db.session.commit()

    return _copy_datafile


def update_datafile_compressed_key_and_column_types(
    datafile_id: str,
    compressed_s3_key: str,
    column_types_as_json: Optional[Dict[str, str]],
):
    datafile = get_datafile(datafile_id)
    if datafile.type != "s3":
        raise Exception(
            "{} datafiles should not have compressed_s3_keys.".format(datafile.type)
        )

    if (
        datafile.format != S3DataFile.DataFileFormat.Columnar
        and column_types_as_json is not None
    ):
        raise Exception(
            "{} datafiles should not have column_types_as_json".format(datafile.format)
        )

    datafile.compressed_s3_key = compressed_s3_key
    datafile.column_types_as_json = column_types_as_json
    db.session.add(datafile)
    db.session.commit()
    return datafile


def add_new_upload_session() -> User:
    user = get_current_session_user()
    us = UploadSession(user_id=user.id)
    db.session.add(us)
    db.session.commit()
    return us


def get_upload_session(session_id: str):
    upload_session = (
        db.session.query(UploadSession).filter(UploadSession.id == session_id).one()
    )
    return upload_session


def get_user_from_upload_session(session_id: str):
    session = (
        db.session.query(UploadSession).filter(UploadSession.id == session_id).one()
    )
    return session.user


def get_upload_session_files_from_session(session_id: str) -> List[UploadSessionFile]:
    # TODO: We could also fetch the datafiles with only one query
    upload_session = (
        db.session.query(UploadSession).filter(UploadSession.id == session_id).one()
    )

    upload_session_files = upload_session.upload_session_files

    # For each upload_session_file, we retrieve its datafile
    return upload_session_files


# </editor-fold>

# <editor-fold desc="Upload Session File">
class EnumS3FolderPath(enum.Enum):
    """Enum which could be useful to have a central way of manipulating the s3 prefixes"""

    Upload = (
        "upload/"
    )  # key prefix which all new uploads are put under.  These are transient until conversion completes
    Convert = (
        "convert/"
    )  # key prefix used for data converted to canonical form.  These are the authorative source.
    Compress = (
        "compressed/"
    )  # key prefix used for compressed raw data.  These are the authorative source.
    Export = (
        "export/"
    )  # key prefix used for results converted for export.  These are transient because they can be re-generated.


def generate_convert_key():
    enumed_convert_path = EnumS3FolderPath.Convert.value
    return os.path.join(enumed_convert_path + str(uuid.uuid4()))


def generate_compressed_key():
    enumed_compressed_path = EnumS3FolderPath.Compress.value
    return os.path.join(enumed_compressed_path + str(uuid.uuid4()))


def add_upload_session_s3_file(
    session_id,
    filename,
    initial_file_type,
    initial_s3_key,
    s3_bucket,
    encoding: Optional[str],
):
    initial_file_type = models.InitialFileType(initial_file_type)

    converted_s3_key = generate_convert_key()
    converted_filetype = models.find_converted_type_by_initial_type(initial_file_type)
    assert converted_filetype is not None

    compressed_s3_key = generate_compressed_key()

    upload_session_file = UploadSessionFile(
        session_id=session_id,
        filename=filename,
        initial_filetype=initial_file_type,
        initial_s3_key=initial_s3_key,
        s3_bucket=s3_bucket,
        converted_s3_key=converted_s3_key,
        converted_filetype=converted_filetype,
        compressed_s3_key=compressed_s3_key,
        encoding=encoding,
    )
    db.session.add(upload_session_file)
    db.session.commit()
    return upload_session_file


def add_upload_session_virtual_file(session_id, filename, data_file_id, commit=True):
    data_file = DataFile.query.get(data_file_id)
    assert data_file is not None

    upload_session_file = UploadSessionFile(
        session_id=session_id, filename=filename, data_file=data_file
    )
    db.session.add(upload_session_file)

    if commit:
        db.session.commit()
    else:
        db.session.flush()

    return upload_session_file


def add_upload_session_gcs_file(session_id, filename, gcs_path, generation_id):
    upload_session_file = UploadSessionFile(
        session_id=session_id,
        filename=filename,
        gcs_path=gcs_path,
        generation_id=generation_id,
    )
    db.session.add(upload_session_file)
    db.session.commit()
    return upload_session_file


def get_upload_session_file(upload_session_file_id):
    upload_session_file = (
        db.session.query(UploadSessionFile)
        .filter(UploadSessionFile.id == upload_session_file_id)
        .one()
    )
    return upload_session_file


def update_upload_session_file_summaries(
    file_id, short_summary, long_summary, column_types, sha256, md5
):
    db.session.query(UploadSessionFile).filter(UploadSessionFile.id == file_id).update(
        dict(
            short_summary=short_summary,
            long_summary=long_summary,
            column_types_as_json=column_types,
            original_file_sha256=sha256,
            original_file_md5=md5,
        )
    )
    db.session.commit()


# </editor-fold>

# <editor-fold desc="Download datafiles">


def _find_cache_entry(dataset_version_id, format, datafile_name):
    entry = (
        db.session.query(ConversionCache)
        .filter(
            and_(
                ConversionCache.dataset_version_id == dataset_version_id,
                ConversionCache.format == format,
                ConversionCache.datafile_name == datafile_name,
            )
        )
        .first()
    )
    return entry


def _add_dl_name(url, dl_name):
    from urllib.parse import urlparse, parse_qsl, urlencode, ParseResult

    p = urlparse(url)
    params = parse_qsl(p.query)
    params.append(("response-content-disposition", "attachment; filename=" + dl_name))

    new_p = ParseResult(
        scheme=p.scheme,
        netloc=p.netloc,
        path=p.path,
        params=p.params,
        query=urlencode(params),
        fragment=p.fragment,
    )

    return new_p.geturl()


def get_signed_urls_from_cache_entry(paths_as_json, dl_filename):
    # if there's urls on the cache entry, report those too after signing them
    if paths_as_json is None or paths_as_json == "":
        return None

    urls = json.loads(paths_as_json)

    if len(urls) == 1:
        dl_filenames = [dl_filename]
    else:
        dl_filenames = ["{}.{}".format(dl_filename, i) for i in range(len(urls))]

    def make_signed_url(url, dl_filename):
        s3_bucket, s3_key = aws.parse_s3_url(url)

        return aws.create_signed_get_obj(s3_bucket, s3_key, dl_filename)

    signed_urls = [
        make_signed_url(url, dl_filename)
        for dl_filename, url in zip(dl_filenames, urls)
    ]
    return signed_urls


def get_conversion_cache_entry(dataset_version_id, datafile_name, format):
    entry = _find_cache_entry(dataset_version_id, format, datafile_name)
    if entry is not None:
        is_new = False
    else:
        is_new = True

        # Create a new cache entry
        status = "Conversion pending"
        entry = ConversionCache(
            dataset_version_id=dataset_version_id,
            datafile_name=datafile_name,
            format=format,
            status=status,
            state=models.ConversionEntryState.running,
        )
        db.session.add(entry)
        db.session.commit()

    assert entry.id is not None
    return is_new, entry


def get_conversion_cache_entry_by_id(entry_id: str) -> ConversionCache:
    return (
        db.session.query(ConversionCache).filter(ConversionCache.id == entry_id).one()
    )


def update_conversion_cache_entry(entry_id, status, urls=None):
    entry = (
        db.session.query(ConversionCache)
        .filter(and_(ConversionCache.id == entry_id))
        .first()
    )
    if urls is not None:
        assert isinstance(urls, list)
        assert len(urls) > 0
        assert isinstance(urls[0], str)
        entry.urls_as_json = json.dumps(urls)
    entry.status = status
    db.session.commit()


def update_conversion_cache_entry_with_task_id(entry_id, task_id):
    db.session.query(ConversionCache).filter(ConversionCache.id == entry_id).update(
        {"task_id": task_id}
    )
    db.session.commit()


def delete_conversion_cache_entry(entry_id):
    db.session.query(ConversionCache).filter(ConversionCache.id == entry_id).delete()
    db.session.commit()


def mark_conversion_cache_entry_as_failed(entry_id):
    db.session.query(ConversionCache).filter(ConversionCache.id == entry_id).update(
        {"state": models.ConversionEntryState.failed}
    )
    db.session.commit()


class IllegalArgumentError(ValueError):
    pass


def find_datafile(
    dataset_permaname, version_number, dataset_version_id, datafile_name
) -> Optional[DataFile]:
    """Look up a datafile given either a permaname (and optional version number) or a dataset_version_id.  The datafile_name
    is also optional.  If unspecified, and there is a single datafile for that dataset_version, that will be returned.
    Otherwise datafile_name is required."""
    if dataset_permaname is not None:
        if dataset_version_id is not None:
            raise IllegalArgumentError(
                "Cannot search by both a permaname and a dataset_version_id"
            )

        if version_number is None:
            try:
                dataset_version = get_latest_dataset_version_by_permaname(
                    dataset_permaname
                )
            except NoResultFound:
                return None
        else:
            try:
                dataset_version = get_dataset_version_by_permaname_and_version(
                    dataset_permaname, version_number
                )
            except NoResultFound:
                return None

        if dataset_version is None:
            return None

        dataset_version_id = dataset_version.id
    else:
        if dataset_version_id is None:
            raise IllegalArgumentError(
                "Must have either a permaname or a dataset_version_id"
            )
        if version_number is not None:
            raise IllegalArgumentError(
                "If permaname is not provided, cannot use version number in search"
            )

        # verify that this is a valid dataset_version_id
        try:
            get_dataset_version(dataset_version_id)
        except NoResultFound:
            return None

    if datafile_name is None:
        dataset_version = get_dataset_version(dataset_version_id)
        if len(dataset_version.datafiles) > 1:
            raise IllegalArgumentError(
                "The retrieved dataset version has more than one datafile so the name must be specified"
            )
        else:
            datafile = list(dataset_version.datafiles)[0]
    else:
        try:
            datafile = get_datafile_by_version_and_name(
                dataset_version_id, datafile_name
            )
        except NoResultFound:
            return None

    return datafile


# </editor-fold>

# <editor-fold desc="Provenance">
def add_graph(
    graph_permaname,
    graph_name,
    graph_user_id=None,
    graph_created_timestamp=None,
    graph_id=None,
):
    assert graph_name

    if not graph_permaname:
        graph_permaname = models.generate_permaname(graph_name)

    # if not graph_user_id:
    #     graph_user_id = get_current_session_user().id

    new_graph = ProvenanceGraph(
        graph_id=graph_id,
        permaname=graph_permaname,
        name=graph_name,
        created_by_user_id=graph_user_id,
        created_timestamp=graph_created_timestamp,
    )

    db.session.add(new_graph)
    db.session.commit()

    return new_graph


def get_provenance_graph(graph_permaname):
    graph = (
        db.session.query(ProvenanceGraph)
        .filter(ProvenanceGraph.permaname == graph_permaname)
        .one_or_none()
    )

    return graph


def get_provenance_graph_by_id(graph_id):
    graph = (
        db.session.query(ProvenanceGraph)
        .filter(ProvenanceGraph.graph_id == graph_id)
        .one()
    )

    return graph


def add_node(graph_id, label, type, node_id=None, datafile_id=None):
    if node_id and get_provenance_node(node_id):
        log.warning("Node {} already exists. Skipping its creation.".format(node_id))
        return get_provenance_node(node_id)

    node_type = models.ProvenanceNode.NodeType(type)

    if node_type == ProvenanceNode.NodeType.Dataset:
        datafile = get_datafile(datafile_id)
    else:
        datafile = None

    new_node = ProvenanceNode(
        node_id=node_id,
        graph_id=graph_id,
        datafile=datafile,
        label=label,
        type=node_type,
    )

    db.session.add(new_node)
    db.session.commit()

    return new_node


def get_provenance_node(node_id):
    node = (
        db.session.query(ProvenanceNode)
        .filter(ProvenanceNode.node_id == node_id)
        .one_or_none()
    )

    return node


def add_edge(from_node_id, to_node_id, edge_id=None, label=None):
    if edge_id and get_provenance_edge(edge_id):
        log.warning("Edge {} already exists. Skipping its creation.".format(edge_id))
        return get_provenance_edge(edge_id)

    new_edge = ProvenanceEdge(
        edge_id=edge_id, from_node_id=from_node_id, to_node_id=to_node_id, label=label
    )
    db.session.add(new_edge)
    db.session.commit()

    return new_edge


def get_provenance_edge(edge_id):
    edge = (
        db.session.query(ProvenanceEdge)
        .filter(ProvenanceEdge.edge_id == edge_id)
        .one_or_none()
    )

    return edge


def is_dataset_node_type(node_type):
    if node_type == ProvenanceNode.NodeType.Dataset.value:
        return True
    else:
        return False


# </editor-fold>

# <editor-fold desc="Utils">


def _get_datetime_from_string(string_datetime):
    return datetime.strptime(string_datetime, "%Y-%m-%d %H:%M:%S.%f")


# </editor-fold>

# <editor-fold desc="UserLog">


def get_entries_access_logs():
    current_user = flask.g.current_user

    array_access_logs = (
        db.session.query(UserLog).filter(UserLog.user_id == current_user.id).all()
    )

    return array_access_logs


def get_entry_access_logs(entryId):
    array_access_logs = (
        db.session.query(UserLog).filter(UserLog.entry_id == entryId).all()
    )

    return array_access_logs


def add_or_update_entry_access_log(entry_id):
    """Create or update, with the current datetime, the access log for the current user, on the entry
    passed in parameter"""

    current_user = flask.g.current_user

    try:
        access_log = (
            db.session.query(UserLog)
            .filter(UserLog.entry_id == entry_id)
            .filter(UserLog.user_id == current_user.id)
            .one_or_none()
        )
    except MultipleResultsFound:
        log.error(
            "When logging access to dataset (id {}) for user {}, we had multiple results instead of only one".format(
                entry_id, current_user.email
            )
        )

    if access_log:
        access_log.last_access = datetime.utcnow()
    else:
        access_log = UserLog(user_id=current_user.id, entry_id=entry_id)

    db.session.add(access_log)
    db.session.commit()

    return access_log


def remove_accessLogs(array_access_log):
    # TODO: Use better way of deleting this
    for access_log in array_access_log:
        db.session.query(UserLog).filter(
            UserLog.entry_id == access_log["entry_id"]
        ).filter(UserLog.user_id == access_log["user_id"]).delete()
    db.session.commit()


# </editor-fold>

# <editor-fold desc="Group">


def user_in_admin_group() -> bool:
    """Return True if the current user is in the admin group"""
    admin_group = get_group_by_name("Admin")
    current_user = get_current_session_user()

    return current_user in admin_group.users


def can_view_group(group_id):
    """Return True if the current user can view the entry"""
    admin_group = get_group_by_name("Admin")
    current_user = get_current_session_user()

    if current_user in admin_group.users:
        return True

    if admin_group.id == group_id:
        # Since we've already determined that current_user is not in admin_group
        return False

    group = get_group(group_id)
    return current_user in group.users


def filter_allowed_groups(groups):
    current_user = get_current_session_user()

    return [group for group in groups if can_view_group(group.id)]


def filtered_joined_groups(groups):
    current_user = get_current_session_user()

    return [group for group in groups if current_user in group.users]


def add_group(name):
    new_group = Group(name=name)
    db.session.add(new_group)
    db.session.commit()

    return new_group


def get_all_groups() -> List[Group]:
    all_groups = db.session.query(Group).all()
    filtered_groups = filter_allowed_groups(all_groups)
    return filtered_groups


def get_all_groups_for_current_user() -> List[Group]:
    all_groups = db.session.query(Group).all()
    filtered_groups = filtered_joined_groups(all_groups)
    return filtered_groups


def get_group(id):
    return db.session.query(Group).filter(Group.id == id).one_or_none()


def get_group_by_name(name):
    return db.session.query(Group).filter(Group.name == name).one_or_none()


def add_group_user_associations(group_id, user_ids):
    current_user = get_current_session_user()
    admin_group = get_group_by_name("Admin")

    if admin_group.id == group_id:
        group = admin_group
    else:
        group = get_group(group_id)
        if not group:
            return None

    assert current_user in group.users or current_user in admin_group.users

    for user_id in user_ids:
        user = get_user(user_id)
        group.users.append(user)

    db.session.commit()
    return group


def remove_group_user_associations(group_id, user_ids):
    current_user = get_current_session_user()
    admin_group = get_group_by_name("Admin")

    if admin_group.id == group_id:
        group = admin_group
    else:
        group = get_group(group_id)
        if not group:
            return None

    assert current_user in group.users or current_user in admin_group.users

    for user_id in user_ids:
        user = get_user(user_id)
        if user in group.users:
            group.users.remove(user)

    db.session.commit()
    return group


def find_matching_name(root_folder, breadcrumbs, search_query) -> List[SearchEntry]:
    matching_entries = []
    # Can't append on a copy()??
    local_breadcrumbs = breadcrumbs.copy()
    local_breadcrumbs.append(Breadcrumb(order=len(breadcrumbs) + 1, folder=root_folder))

    for entry in root_folder.entries:
        if search_query.lower() in entry.name.lower():
            search_entry = SearchEntry(entry=entry, breadcrumbs=local_breadcrumbs)
            matching_entries.append(search_entry)

        # If this is a folder, we enter into it and search inside it
        if isinstance(entry, Folder):
            # We need to be mindful about the same folder being in itself => Infinite recursion
            already_in = any(
                [breadcrumb.folder.id == entry.id for breadcrumb in local_breadcrumbs]
            )

            if not already_in:
                matching_entries.extend(
                    find_matching_name(entry, local_breadcrumbs, search_query)
                )

    return matching_entries


def get_activity_for_dataset_id(dataset_id):
    return (
        db.session.query(Activity).filter(Activity.dataset_id == dataset_id)
        # .order_by(Activity.timestamp.desc())
        .all()
    )


def get_figshare_personal_token_for_current_user() -> Optional[str]:
    current_user = get_current_session_user()
    return current_user.figshare_personal_token


def add_figshare_token(token: str) -> bool:
    current_user = get_current_session_user()
    is_new = current_user.figshare_personal_token != token
    current_user.figshare_personal_token = token

    db.session.add(current_user)
    db.session.commit()
    return is_new


def remove_figshare_token_for_current_user():
    current_user = get_current_session_user()
    current_user.figshare_personal_token = None
    db.session.add(current_user)
    db.session.commit()


def add_figshare_dataset_version_link(
    dataset_version_id: str, figshare_article_id: int, figshare_article_version: int
):
    current_user = get_current_session_user()
    figshare_dataset_version_link = FigshareDatasetVersionLink(
        figshare_article_id=figshare_article_id,
        figshare_article_version=figshare_article_version,
        dataset_version_id=dataset_version_id,
        creator_id=current_user.id,
    )

    db.session.add(figshare_dataset_version_link)
    db.session.commit()

    return figshare_dataset_version_link


def add_figshare_datafile_link(
    datafile_id: str, figshare_file_id: int, figshare_dataset_version_link_id: str
):
    figshare_datafile_link = FigshareDataFileLink(
        figshare_file_id=figshare_file_id,
        datafile_id=datafile_id,
        figshare_dataset_version_link_id=figshare_dataset_version_link_id,
    )

    db.session.add(figshare_datafile_link)
    db.session.commit()

    return figshare_datafile_link


def get_figshare_datafile_links_for_dataset_version_link(
    figshare_dataset_version_link_id: str,
) -> List[FigshareDataFileLink]:
    figshare_datafile_links = (
        db.session.query(FigshareDataFileLink)
        .filter(
            FigshareDataFileLink.figshare_dataset_version_link_id
            == figshare_dataset_version_link_id
        )
        .all()
    )

    return figshare_datafile_links


def get_figshare_datafile_link_by_figshare_id(
    figshare_id: str,
) -> FigshareDataFileLink:
    figshare_datafile_link = (
        db.session.query(FigshareDataFileLink)
        .filter(FigshareDataFileLink.figshare_file_id == figshare_id)
        .one_or_none()
    )

    return figshare_datafile_link


def delete_figshare_dataset_version_and_datafiles(
    figshare_dataset_version_link_id: str,
):
    dataset_version_link = (
        db.session.query(FigshareDatasetVersionLink)
        .filter(FigshareDatasetVersionLink.id == figshare_dataset_version_link_id)
        .one_or_none()
    )
    datafile_links = get_figshare_datafile_links_for_dataset_version_link(
        figshare_dataset_version_link_id
    )
    for datafile_link in datafile_links:
        db.session.delete(datafile_link)

    if dataset_version_link is not None:
        db.session.delete(dataset_version_link)

    db.session.commit()
    return True


def get_dataset_subscription(subscription_id: str) -> Optional[DatasetSubscription]:
    return (
        db.session.query(DatasetSubscription)
        .filter(DatasetSubscription.id == subscription_id)
        .one_or_none()
    )


def get_dataset_subscriptions_for_user(user_id: str) -> List[DatasetSubscription]:
    return (
        db.session.query(DatasetSubscription)
        .filter(DatasetSubscription.user_id == user_id)
        .all()
    )


def get_dataset_subscriptions_for_dataset(dataset_id: str) -> List[DatasetSubscription]:
    return (
        db.session.query(DatasetSubscription)
        .filter(DatasetSubscription.dataset_id == dataset_id)
        .all()
    )


def get_dataset_subscription_for_dataset_and_user(
    dataset_id: str, user_id: Optional[str] = None
) -> Optional[DatasetSubscription]:
    if user_id is None:
        current_user = get_current_session_user()
        user_id = current_user.id

    return (
        db.session.query(DatasetSubscription)
        .filter(DatasetSubscription.user_id == user_id)
        .filter(DatasetSubscription.dataset_id == dataset_id)
        .one_or_none()
    )


def add_dataset_subscription(dataset_id: str) -> Tuple[DatasetSubscription, bool]:
    current_user = get_current_session_user()
    subscription = get_dataset_subscription_for_dataset_and_user(
        dataset_id, current_user.id
    )
    if subscription is not None:
        return subscription, False

    subscription = DatasetSubscription(user_id=current_user.id, dataset_id=dataset_id)
    db.session.add(subscription)
    db.session.commit()
    return subscription, True


def delete_dataset_subscription(subscription_id: str) -> bool:
    current_user = get_current_session_user()
    subscription = get_dataset_subscription(subscription_id)

    if subscription is None:
        return False

    if subscription.user_id != current_user.id:
        return False

    db.session.delete(subscription)
    db.session.commit()
    return True
