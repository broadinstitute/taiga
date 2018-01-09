from datetime import datetime
import enum
import flask
import uuid
import os

import json

from sqlalchemy import and_, update

import taiga2.models as models
from taiga2.models import db
from taiga2 import aws
from taiga2.models import User, Folder, Dataset, DataFile, DatasetVersion, Entry
from taiga2.models import UploadSession, UploadSessionFile, ConversionCache
from taiga2.models import UserLog
from taiga2.models import ProvenanceGraph, ProvenanceNode, ProvenanceEdge

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm.session import make_transient
from sqlalchemy.sql.expression import func

import logging

log = logging.getLogger(__name__)


# IMPORTANT:
#   If you have this error "RuntimeError: application not registered on db instance and
#   no application bound to current context" while trying around within command line,
#   You need to push the context of you app => app.app_context().push() (for us frontend_app.app_context().push()

# <editor-fold desc="User">
def add_user(name, email):
    new_user = User(name=name,
                    email=email)

    home_description = """Welcome to Taiga2: a light-weight repository for capturing, versioning and accessing datasets.

Make yourself comfortable, you're at Home."""

    home_folder = Folder(name="Home",
                         description=home_description,
                         folder_type=models.Folder.FolderType.home,
                         creator=new_user)

    trash_folder = Folder(name="Trash",
                          folder_type=Folder.FolderType.trash,
                          creator=new_user)

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


def get_current_session_user():
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
def add_folder(name,
               folder_type,
               description):
    creator = get_current_session_user()

    new_folder = Folder(name=name,
                        folder_type=folder_type,
                        description=description,
                        creator=creator)
    db.session.add(new_folder)
    db.session.commit()

    return new_folder


def get_folder(folder_id, one_or_none=False):
    query = db.session.query(Folder).filter(Folder.id == folder_id)
    return _fetch_respecting_one_or_none(q=query, one_or_none=one_or_none)


def get_folder_by_name(folder_name):
    """Get the folder by name of the current_user in the session. If multiple folders with the same name exist,
    returns the first one"""
    current_user = get_current_session_user()
    folder = db.session.query(Folder).filter(Folder.creator_id == current_user.id) \
        .filter(Folder.name == folder_name) \
        .first()

    if folder is None:
        raise NoResultFound
    else:
        return folder


def get_public_folder():
    public_folder = db.session.query(Folder).filter(Folder.id == 'public').first()
    return public_folder


def update_folder_name(folder_id, new_name):
    folder = get_folder(folder_id)

    folder.name = new_name
    db.session.add(folder)
    db.session.commit()

    return folder


def update_folder_description(folder_id, new_description):
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
    entry = db.session.query(Entry) \
        .filter(Entry.id == entry_id).one()
    parent_folders = entry.parents

    return parent_folders


# </editor-fold>

# <editor-fold desc="Dataset">
def add_dataset(name,
                description,
                datafiles_ids=None,
                permaname=None,
                anterior_creation_date=None):
    # assert len(datafiles_ids) > 0

    if not permaname:
        permaname = models.generate_permaname(name)

    creator = get_current_session_user()

    creation_date = None
    if anterior_creation_date:
        creation_date = anterior_creation_date

    new_dataset = Dataset(name=name,
                          permaname=permaname,
                          description=description,
                          creator=creator,
                          creation_date=creation_date)

    db.session.add(new_dataset)

    # It means we would want to create a first dataset with a DatasetVersion
    # containing DataFiles

    # TODO: Think about a meaningful name
    if datafiles_ids is not None:
        db.session.flush()
        new_dataset_version = add_dataset_version(dataset_id=new_dataset.id,
                                                  datafiles_ids=datafiles_ids,
                                                  new_description=description,
                                                  anterior_creation_date=creation_date)

        db.session.add(new_dataset_version)

    db.session.commit()

    # Add the related activity
    # TODO: Add the activity
    # TODO: Think about an automatic way of adding/updating the activity
    return new_dataset


def add_dataset_from_session(session_id, dataset_name, dataset_description, current_folder_id):
    added_datafiles = add_datafiles_from_session(session_id)

    # TODO: Get the user from the session
    user = get_user_from_upload_session(session_id)
    dataset_permaname = models.generate_permaname(dataset_name)
    added_dataset = add_dataset(name=dataset_name,
                                permaname=dataset_permaname,
                                description=dataset_description,
                                datafiles_ids=[datafile.id
                                               for datafile in added_datafiles])
    add_folder_entry(current_folder_id, added_dataset.id)

    return added_dataset


def get_dataset(dataset_id, one_or_none=False):
    q = db.session.query(Dataset) \
        .filter(Dataset.id == dataset_id)
    return _fetch_respecting_one_or_none(q, one_or_none)


def get_datasets(array_dataset_ids):
    datasets = db.session.query(Dataset) \
        .filter(Dataset.id.in_(array_dataset_ids)).all()

    return datasets


def get_dataset_from_permaname(dataset_permaname, one_or_none=False):
    q = db.session.query(Dataset) \
        .filter(Dataset.permaname == dataset_permaname)

    return _fetch_respecting_one_or_none(q, one_or_none)


def get_first_dataset_version(dataset_id):
    dataset_version_first = db.session.query(DatasetVersion) \
        .filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.version == 1).one()

    return dataset_version_first


def get_latest_dataset_version(dataset_id):
    dataset = get_dataset(dataset_id)
    max_version = 0
    dataset_version_latest_version = None
    for dataset_version in dataset.dataset_versions:
        if dataset_version.version > max_version:
            dataset_version_latest_version = dataset_version
            max_version = dataset_version.version

    return dataset_version_latest_version


def update_dataset_name(dataset_id, name):
    dataset = get_dataset(dataset_id)

    dataset.name = name
    # TODO: Update the permaname with the new name
    # TODO: Update the activity

    db.session.add(dataset)
    db.session.commit()

    return dataset


def update_dataset_description(dataset_id, description):
    dataset = get_dataset(dataset_id)

    dataset.description = description

    db.session.add(dataset)
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


def update_dataset_contents(dataset_id,
                            datafiles_id_to_remove=None,
                            datafiles_id_to_add=None,
                            new_description=None,
                            comments="No comments"):
    # TODO: Does it make sense to have a "add datafiles?". Each datafile belongs to a dataset_version
    if not datafiles_id_to_remove:
        datafiles_id_to_remove = []
    if not datafiles_id_to_add:
        datafiles_id_to_add = []

    # Fetch the entries to remove
    datafiles_to_remove = [get_datafile(datafile_id_to_remove)
                           for datafile_id_to_remove in datafiles_id_to_remove]

    # Fetch the entries to add
    datafiles_to_add = [get_datafile(datafile_id_to_add)
                        for datafile_id_to_add in datafiles_id_to_add]

    dataset = get_dataset(dataset_id)

    # Fetch the last version
    # TODO: Make a function to retrieve the last version
    # TODO: Improve this using db.session.query => OperationalError currently
    max_version = 0
    dataset_version_latest_version = None
    for dataset_version in dataset.dataset_versions:
        if dataset_version.version > max_version:
            dataset_version_latest_version = dataset_version

    _description = dataset.description

    if new_description is not None:
        _description = new_description

    # latest_version_datafiles = dataset_version_latest_version.datafiles

    # Create the new dataset_version from the latest and update its version
    # TODO: Remove the increment of the version since it should be handled by add_dataset_version directly
    new_updated_dataset_version = add_dataset_version(dataset_id=dataset_version_latest_version.dataset.id,
                                                      datafiles_ids=[datafile.id
                                                                     for datafile in
                                                                     dataset_version_latest_version.datafiles],
                                                      new_description=_description)

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


def add_or_update_dataset_access_log(dataset_id):
    """Create or update, with the current datetime, the access log for the current user, on the dataset
    passed in parameter"""

    current_user = flask.g.current_user

    try:
        access_log = db.session.query(UserLog) \
            .filter(UserLog.dataset_id == dataset_id) \
            .filter(UserLog.user_id == current_user.id) \
            .one_or_none()
    except MultipleResultsFound:
        log.error("When logging access to dataset (id {}) for user {}, we had multiple results instead of only one" \
                  .format(dataset_id, current_user.email)
                  )

    if access_log:
        access_log.last_access = datetime.utcnow()
    else:
        access_log = UserLog(user_id=current_user.id,
                             dataset_id=dataset_id)

    db.session.add(access_log)
    db.session.commit()

    return access_log


def get_datasets_access_logs():
    current_user = flask.g.current_user

    array_access_logs = db.session.query(UserLog) \
        .filter(UserLog.user_id == current_user.id).all()

    return array_access_logs


# </editor-fold>

# <editor-fold desc="DatasetVersion">
def add_dataset_version(dataset_id,
                        datafiles_ids=None,
                        new_description=None,
                        permaname=None,
                        anterior_creation_date=None,
                        forced_id=None):
    assert len(datafiles_ids) > 0
    assert isinstance(datafiles_ids, list)

    # Fetch the object from the database
    creator = get_current_session_user()

    dataset = get_entry(dataset_id)

    datafiles = db.session.query(DataFile) \
        .filter(DataFile.id.in_(datafiles_ids)).all()

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

    _description = new_description

    if _description is None:
        _description = dataset.description

    # Create the DatasetVersion object
    new_dataset_version = DatasetVersion(name=name,
                                         creator=creator,
                                         dataset=dataset,
                                         datafiles=datafiles,
                                         description=new_description,
                                         version=version,
                                         creation_date=creation_date,
                                         id=forced_id)

    # We now update the dataset description with the latest datasetVersion description
    # TODO: We should probably remove the description of a dataset, to use only the DatasetVersion one
    if new_description is not None:
        dataset.description = _description
        db.session.add(new_dataset_version)

    db.session.add(dataset)
    db.session.commit()

    return new_dataset_version


def create_new_dataset_version_from_session(session_id,
                                            dataset_id,
                                            existing_datafiles_id,
                                            new_description=None):
    added_datafiles = add_datafiles_from_session(session_id)
    added_datafile_ids = [datafile.id for datafile in added_datafiles]

    copied_existing_datafiles_ids = [copy_datafile(original_datafile).id
                                     for original_datafile in existing_datafiles_id]

    all_datafile_ids = added_datafile_ids + copied_existing_datafiles_ids

    _description = None

    # If the description if filled it means we want to change it, otherwise we take the dataset one
    # TODO: It would be less dangerous to take the latest datasetVersion description
    if new_description is not None:
        _description = new_description
    else:
        _description = get_entry(dataset_id).description

    new_dataset_version = add_dataset_version(dataset_id=dataset_id,
                                              datafiles_ids=all_datafile_ids,
                                              new_description=_description)

    return new_dataset_version


def _fetch_respecting_one_or_none(q, one_or_none):
    """If one_or_none is set, asks the query q to return none if NoResultFound, else raise the error"""
    if one_or_none:
        return q.one_or_none()
    else:
        return q.one()


def get_dataset_version(dataset_version_id, one_or_none=False):
    q = db.session.query(DatasetVersion) \
        .filter(DatasetVersion.id == dataset_version_id)

    return _fetch_respecting_one_or_none(q, one_or_none)


def get_dataset_versions(dataset_id):
    dataset_versions = db.session.query(DatasetVersion) \
        .filter(DatasetVersion.dataset_id == dataset_id) \
        .all()

    return dataset_versions


def get_dataset_versions_bulk(array_dataset_version_ids):
    dataset_versions = db.session.query(DatasetVersion) \
        .filter(DatasetVersion.id.in_(array_dataset_version_ids)).all()

    return dataset_versions


def get_dataset_version_provenance(dataset_version_id,
                                   provenance):
    # TODO: See how to manage the provenance
    raise NotImplementedError


def get_latest_dataset_version_by_permaname(permaname):
    dataset_version = db.session.query(DatasetVersion) \
        .filter(DatasetVersion.dataset.has(Dataset.permaname == permaname)) \
        .order_by(DatasetVersion.version.desc()) \
        .first()

    return dataset_version


def get_dataset_version_by_permaname_and_version(permaname,
                                                 version, one_or_none=False):
    """From the permaname of a dataset, retrieve the specific dataset version"""
    # dataset = get_dataset_from_permaname(permaname)
    q = db.session.query(DatasetVersion) \
        .filter(DatasetVersion.version == version) \
        .filter(DatasetVersion.dataset.has(Dataset.permaname == permaname))

    return _fetch_respecting_one_or_none(q, one_or_none)


def get_dataset_version_by_dataset_id_and_dataset_version_id(dataset_id,
                                                             dataset_version_id, one_or_none=False):
    dataset_version = get_dataset_version(dataset_version_id, one_or_none=one_or_none)

    return dataset_version


def update_dataset_version_description(dataset_version_id,
                                       new_description):
    dataset_version = get_dataset_version(dataset_version_id)

    dataset_version.description = new_description

    db.session.add(dataset_version)
    db.session.commit()

    return dataset_version


# </editor-fold>

# <editor-fold desc="Entry">
def get_entry(entry_id):
    entry = db.session.query(Entry) \
        .filter(Entry.id == entry_id) \
        .one()

    return entry


class EntryAction(enum.Enum):
    move = 1
    copy = 2


def _action_to_folder(entry_ids, target_folder_id, entry_action, current_folder_id=None):
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

    _action_to_folder(entry_ids=entry_ids, folder_id=trash_folder.id, entry_action=EntryAction.move)


def move_to_folder(entry_ids, current_folder_id, target_folder_id):
    # If we don't get a target_folder_id, it means we want to put it into the trash
    if not target_folder_id:
        # Get the current user's trash folder
        current_user = get_current_session_user()
        trash_folder = current_user.trash_folder

        target_folder_id = trash_folder.id

    # TODO: Check if the user is allowed to do this?
    _action_to_folder(entry_ids=entry_ids,
                      current_folder_id=current_folder_id,
                      target_folder_id=target_folder_id,
                      entry_action=EntryAction.move)


def copy_to_folder(entry_ids, target_folder_id):
    _action_to_folder(entry_ids=entry_ids,
                      target_folder_id=target_folder_id,
                      entry_action=EntryAction.copy)


def changer_owner(entry_id, new_creator_id):
    entry = get_entry(entry_id)
    entry.creator_id = new_creator_id

    db.session.add(entry)
    db.session.commit()


def already_seen(entry_id):
    """Return True if the current user has already seen the entry"""
    visited_list = db.session.query(UserLog) \
        .filter(UserLog.entry_id == entry_id) \
        .filter(UserLog.user == get_current_session_user()) \
        .all()

    if visited_list:
        return True
    else:
        return False


def can_view(entry_id):
    """Return True if the current user can view the entry"""
    entry = get_entry(entry_id=entry_id)

    current_user = get_current_session_user()

    public_folder = get_entry('public')

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
def add_datafile(s3_bucket,
                 s3_key,
                 name,
                 type,
                 short_summary,
                 long_summary,
                 forced_id=None):
    received_type = type
    # TODO: See register_datafile_id
    new_datafile_name = name
    # We try to manage properly the type
    if not isinstance(received_type, models.DataFile.DataFileType):
        for data_file_type in models.DataFile.DataFileType:
            if str.lower(data_file_type.value) == str.lower(type):
                received_type = data_file_type

    if not isinstance(received_type, models.DataFile.DataFileType):
        message = "The type does not match an allowed one"
        log.error(message)
        raise Exception(message)

    new_datafile = DataFile(name=new_datafile_name,
                            s3_bucket=s3_bucket,
                            s3_key=s3_key,
                            type=received_type,
                            short_summary=short_summary,
                            long_summary=long_summary,
                            id=forced_id)

    db.session.add(new_datafile)
    db.session.commit()

    return new_datafile


def get_datafile_by_version_and_name(dataset_version_id, name):
    return db.session.query(DataFile).filter(DataFile.name == name) \
        .filter(DataFile.dataset_version_id == dataset_version_id) \
        .one()


def get_datafile(datafile_id):
    datafile = db.session.query(DataFile) \
        .filter(DataFile.id == datafile_id).one()

    return datafile


def get_latest_version_datafiles_from_dataset(dataset_id):
    dataset = get_dataset(dataset_id)

    latest_dataset_version = dataset.dataset_versions[-1]

    return latest_dataset_version.datafiles


def add_datafiles_from_session(session_id):
    # We retrieve all the upload_session_files related to the UploadSession
    added_files = get_upload_session_files_from_session(session_id)

    # Generate the datafiles from these files
    added_datafiles = []
    for file in added_files:
        new_datafile = add_datafile(name=file.filename,
                                    s3_bucket=file.s3_bucket,
                                    s3_key=file.converted_s3_key,
                                    type=file.converted_filetype,
                                    short_summary=file.short_summary,
                                    long_summary=file.long_summary)
        added_datafiles.append(new_datafile)

    return added_datafiles


def copy_datafile(original_datafile_id):
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


# </editor-fold>

# <editor-fold desc="Upload Session">
def add_new_upload_session():
    user = get_current_session_user()
    us = UploadSession(user_id=user.id)
    db.session.add(us)
    db.session.commit()
    return us


def get_upload_session(session_id):
    upload_session = db.session.query(UploadSession).filter(UploadSession.id == session_id).one()
    return upload_session


def get_user_from_upload_session(session_id):
    session = db.session.query(UploadSession).filter(UploadSession.id == session_id).one()
    return session.user


def get_upload_session_files_from_session(session_id):
    # TODO: We could also fetch the datafiles with only one query
    upload_session = db.session.query(UploadSession) \
        .filter(UploadSession.id == session_id).one()

    upload_session_files = upload_session.upload_session_files

    # For each upload_session_file, we retrieve its datafile
    return upload_session_files


# </editor-fold>

# <editor-fold desc="Upload Session File">
class EnumS3FolderPath(enum.Enum):
    """Enum which could be useful to have a central way of manipulating the s3 prefixes"""
    Upload = 'upload/'  # key prefix which all new uploads are put under.  These are transient until conversion completes
    Convert = 'convert/'  # key prefix used for data converted to canonical form.  These are the authorative source.
    Export = 'export/'  # key prefix used for results converted for export.  These are transient because they can be re-generated.


def generate_convert_key():
    enumed_convert_path = EnumS3FolderPath.Convert.value
    return os.path.join(enumed_convert_path + str(uuid.uuid4()))


def add_upload_session_file(session_id, filename, initial_file_type, initial_s3_key, s3_bucket):
    initial_file_type = models.InitialFileType(initial_file_type)

    converted_s3_key = generate_convert_key()

    upload_session_file = UploadSessionFile(session_id=session_id,
                                            filename=filename,
                                            initial_filetype=initial_file_type,
                                            initial_s3_key=initial_s3_key,
                                            s3_bucket=s3_bucket,
                                            converted_s3_key=converted_s3_key,
                                            converted_filetype=models.find_converted_type_by_initial_type(
                                                initial_file_type))
    db.session.add(upload_session_file)
    db.session.commit()
    return upload_session_file


def get_upload_session_file(upload_session_file_id):
    upload_session_file = db.session.query(UploadSessionFile) \
        .filter(UploadSessionFile.id == upload_session_file_id).one()
    return upload_session_file


def update_upload_session_file_summaries(file_id, short_summary, long_summary):
    db.session.query(UploadSessionFile).filter(UploadSessionFile.id == file_id).update(
        dict(short_summary=short_summary, long_summary=long_summary))
    db.session.commit()


# </editor-fold>

# <editor-fold desc="Download datafiles">


def _find_cache_entry(dataset_version_id, format, datafile_name):
    entry = db.session.query(ConversionCache).filter(and_(ConversionCache.dataset_version_id == dataset_version_id,
                                                          ConversionCache.format == format,
                                                          ConversionCache.datafile_name == datafile_name)).first()
    return entry


def _add_dl_name(url, dl_name):
    from urllib.parse import urlparse, parse_qsl, urlencode, ParseResult

    p = urlparse(url)
    params = parse_qsl(p.query)
    params.append(("response-content-disposition", "attachment; filename=" + dl_name))

    new_p = ParseResult(scheme=p.scheme, netloc=p.netloc, path=p.path,
                        params=p.params, query=urlencode(params), fragment=p.fragment)

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

    signed_urls = [make_signed_url(url, dl_filename) for dl_filename, url in zip(dl_filenames, urls)]
    return signed_urls


def get_conversion_cache_entry(dataset_version_id, datafile_name, format):
    entry = _find_cache_entry(dataset_version_id, format, datafile_name)
    if entry is not None:
        is_new = False
    else:
        is_new = True

        # Create a new cache entry
        status = "Conversion pending"
        entry = ConversionCache(dataset_version_id=dataset_version_id,
                                datafile_name=datafile_name,
                                format=format,
                                status=status,
                                state=models.ConversionEntryState.running)
        db.session.add(entry)
        db.session.commit()

    assert entry.id is not None
    return is_new, entry


def update_conversion_cache_entry(entry_id, status, urls=None):
    entry = db.session.query(ConversionCache).filter(and_(ConversionCache.id == entry_id)).first()
    if urls is not None:
        assert isinstance(urls, list)
        assert len(urls) > 0
        assert isinstance(urls[0], str)
        entry.urls_as_json = json.dumps(urls)
    entry.status = status
    db.session.commit()


def update_conversion_cache_entry_with_task_id(entry_id, task_id):
    db.session.query(ConversionCache). \
        filter(ConversionCache.id == entry_id). \
        update({"task_id": task_id})
    db.session.commit()


def delete_conversion_cache_entry(entry_id):
    db.session.query(ConversionCache). \
        filter(ConversionCache.id == entry_id). \
        delete()
    db.session.commit()


def mark_conversion_cache_entry_as_failed(entry_id):
    db.session.query(ConversionCache). \
        filter(ConversionCache.id == entry_id). \
        update({"state": models.ConversionEntryState.failed})
    db.session.commit()


class IllegalArgumentError(ValueError):
    pass


def find_datafile(dataset_permaname, version_number, dataset_version_id, datafile_name):
    """Look up a datafile given either a permaname (and optional version number) or a dataset_version_id.  The datafile_name
    is also optional.  If unspecified, and there is a single datafile for that dataset_version, that will be returned.
    Otherwise datafile_name is required. """
    if dataset_permaname is not None:
        if dataset_version_id is not None:
            raise IllegalArgumentError("Cannot search by both a permaname and a dataset_version_id")

        if version_number is None:
            try:
                dataset_version = get_latest_dataset_version_by_permaname(dataset_permaname)
            except NoResultFound:
                return None
        else:
            try:
                dataset_version = get_dataset_version_by_permaname_and_version(dataset_permaname, version_number)
            except NoResultFound:
                return None

        if dataset_version is None:
            return None

        dataset_version_id = dataset_version.id
    else:
        if dataset_version_id is None:
            raise IllegalArgumentError("Must have either a permaname or a dataset_version_id")
        if version_number is not None:
            raise IllegalArgumentError("If permaname is not provided, cannot use version number in search")

        # verify that this is a valid dataset_version_id
        try:
            get_dataset_version(dataset_version_id)
        except NoResultFound:
            return None

    if datafile_name is None:
        dataset_version = get_dataset_version(dataset_version_id)
        if len(dataset_version.datafiles) > 1:
            raise IllegalArgumentError(
                "The retrieved dataset version has more than one datafile so the name must be specified")
        else:
            datafile = list(dataset_version.datafiles)[0]
    else:
        try:
            datafile = get_datafile_by_version_and_name(dataset_version_id, datafile_name)
        except NoResultFound:
            return None

    return datafile


# </editor-fold>

# <editor-fold desc="Provenance">
def add_graph(graph_permaname, graph_name,
              graph_user_id=None, graph_created_timestamp=None,
              graph_id=None):
    assert graph_name

    if not graph_permaname:
        graph_permaname = models.generate_permaname(graph_name)

    # if not graph_user_id:
    #     graph_user_id = get_current_session_user().id

    new_graph = ProvenanceGraph(graph_id=graph_id,
                                permaname=graph_permaname,
                                name=graph_name,
                                created_by_user_id=graph_user_id,
                                created_timestamp=graph_created_timestamp)

    db.session.add(new_graph)
    db.session.commit()

    return new_graph


def get_provenance_graph(graph_permaname):
    graph = db.session.query(ProvenanceGraph) \
        .filter(ProvenanceGraph.permaname == graph_permaname) \
        .one_or_none()

    return graph


def get_provenance_graph_by_id(graph_id):
    graph = db.session.query(ProvenanceGraph) \
        .filter(ProvenanceGraph.graph_id == graph_id) \
        .one()

    return graph


def add_node(graph_id,
             label, type,
             node_id=None, datafile_id=None):
    if node_id and get_provenance_node(node_id):
        log.warning("Node {} already exists. Skipping its creation.".format(node_id))
        return get_provenance_node(node_id)

    node_type = models.ProvenanceNode.NodeType(type)

    if node_type == ProvenanceNode.NodeType.Dataset:
        datafile = get_datafile(datafile_id)
    else:
        datafile = None

    new_node = ProvenanceNode(node_id=node_id,
                              graph_id=graph_id,
                              datafile=datafile,
                              label=label,
                              type=node_type)

    db.session.add(new_node)
    db.session.commit()

    return new_node


def get_provenance_node(node_id):
    node = db.session.query(ProvenanceNode) \
        .filter(ProvenanceNode.node_id == node_id) \
        .one_or_none()

    return node


def add_edge(from_node_id, to_node_id,
             edge_id=None, label=None):
    if edge_id and get_provenance_edge(edge_id):
        log.warning("Edge {} already exists. Skipping its creation.".format(edge_id))
        return get_provenance_edge(edge_id)

    new_edge = ProvenanceEdge(edge_id=edge_id,
                              from_node_id=from_node_id,
                              to_node_id=to_node_id,
                              label=label)
    db.session.add(new_edge)
    db.session.commit()

    return new_edge


def get_provenance_edge(edge_id):
    edge = db.session.query(ProvenanceEdge) \
        .filter(ProvenanceEdge.edge_id == edge_id) \
        .one_or_none()

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

    array_access_logs = db.session.query(UserLog) \
        .filter(UserLog.user_id == current_user.id).all()

    return array_access_logs


def get_entry_access_logs(entryId):
    array_access_logs = db.session.query(UserLog) \
        .filter(UserLog.entry_id == entryId).all()

    return array_access_logs


def add_or_update_entry_access_log(entry_id):
    """Create or update, with the current datetime, the access log for the current user, on the entry
    passed in parameter"""

    current_user = flask.g.current_user

    try:
        access_log = db.session.query(UserLog) \
            .filter(UserLog.entry_id == entry_id) \
            .filter(UserLog.user_id == current_user.id) \
            .one_or_none()
    except MultipleResultsFound:
        log.error("When logging access to dataset (id {}) for user {}, we had multiple results instead of only one" \
                  .format(entry_id, current_user.email)
                  )

    if access_log:
        access_log.last_access = datetime.utcnow()
    else:
        access_log = UserLog(user_id=current_user.id,
                             entry_id=entry_id)

    db.session.add(access_log)
    db.session.commit()

    return access_log


def remove_accessLogs(array_access_log):
    # TODO: Use better way of deleting this
    for access_log in array_access_log:
        db.session.query(UserLog) \
            .filter(UserLog.entry_id == access_log['entry_id']) \
            .filter(UserLog.user_id == access_log['user_id']) \
            .delete()
    db.session.commit()

# </editor-fold>
