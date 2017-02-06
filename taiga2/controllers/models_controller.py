import enum
import uuid
import os

import json

from sqlalchemy import and_

import taiga2.models as models
from taiga2.models import db
from taiga2 import aws
from taiga2.models import User, Folder, Dataset, DataFile, DatasetVersion, Entry
from taiga2.models import UploadSession, UploadSessionFile, ConversionCache

from sqlalchemy.sql.expression import func


# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)

# IMPORTANT:
#   If you have this error "RuntimeError: application not registered on db instance and
#   no application bound to current context" while trying around within command line,
#   You need to push the context of you app => app.app_context().push() (for us frontend_app.app_context().push()

# <editor-fold desc="User">
def add_user(name):
    new_user = User(name=name)

    home_folder = Folder(name="Home",
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


# </editor-fold>

# <editor-fold desc="Folder">
def add_folder(creator_id=None,
               name="Untitled Folder",
               folder_type=Folder.FolderType.folder,
               description="No description provided"):
    creator = get_user(creator_id)

    new_folder = Folder(name=name,
                        folder_type=folder_type,
                        description=description,
                        creator=creator)
    db.session.add(new_folder)
    db.session.commit()

    return new_folder


def get_folder(folder_id):
    return db.session.query(Folder).filter(Folder.id == folder_id).first()


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
                creator_id=None,
                permaname=None,
                description="No description provided",
                datafiles_ids=None):
    assert len(datafiles_ids) > 0

    if not permaname:
        permaname = models.generate_permaname(name)

    creator = get_user(creator_id)
    new_dataset = Dataset(name=name,
                          permaname=permaname,
                          description=description,
                          creator=creator)

    db.session.add(new_dataset)
    db.session.flush()

    # It means we would want to create a first dataset with a DatasetVersion
    # containing DataFiles

    # TODO: Think about a meaningful name
    new_dataset_version = add_dataset_version(creator_id=creator.id,
                                              dataset_id=new_dataset.id,
                                              datafiles_ids=datafiles_ids)

    db.session.add(new_dataset_version)
    db.session.commit()

    # Add the related activity
    # TODO: Add the activity
    # TODO: Think about an automatic way of adding/updating the activity
    return new_dataset


def add_dataset_from_session(session_id, dataset_name, dataset_description, current_folder_id):
    # We retrieve all the upload_session_files related to the UploadSession
    added_files = get_upload_session_files_from_session(session_id)

    # Generate the datafiles from these files
    added_datafiles = []
    for file in added_files:
        new_datafile = add_datafile(name=file.filename,
                                    url=file.url,
                                    s3_bucket=file.converted_s3_bucket,
                                    s3_key=file.converted_s3_key,
                                    type=file.converted_filetype)
        added_datafiles.append(new_datafile)

    # TODO: Get the user from the session
    admin = get_user_from_upload_session(session_id)
    dataset_permaname = models.generate_permaname(dataset_name)
    added_dataset = add_dataset(creator_id=admin.id,
                                name=dataset_name,
                                permaname=dataset_permaname,
                                description=dataset_description,
                                datafiles_ids=[datafile.id
                                               for datafile in added_datafiles])
    updated_folder = add_folder_entry(current_folder_id,
                                      added_dataset.id)

    return added_dataset


def get_dataset(dataset_id):
    dataset = db.session.query(Dataset) \
        .filter(Dataset.id == dataset_id).one()

    return dataset


def get_dataset_from_permaname(dataset_permaname):
    dataset = db.session.query(Dataset) \
        .filter(Dataset.permaname == dataset_permaname) \
        .one()

    return dataset


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


# TODO: update_datafile_summaries
# def update_datafile_summaries


def update_dataset_contents(dataset_id,
                            datafiles_id_to_remove=None,
                            datafiles_id_to_add=None,
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

    # latest_version_datafiles = dataset_version_latest_version.datafiles

    # Create the new dataset_version from the latest and update its version
    # TODO: Remove the increment of the version since it should be handled by add_dataset_version directly
    new_updated_dataset_version = add_dataset_version(creator_id=dataset_version_latest_version.creator.id,
                                                      dataset_id=dataset_version_latest_version.dataset.id,
                                                      datafiles_ids=[datafile.id
                                                                     for datafile in
                                                                     dataset_version_latest_version.datafiles])

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


# </editor-fold>

# <editor-fold desc="DatasetVersion">
def add_dataset_version(creator_id,
                        dataset_id,
                        datafiles_ids=None,
                        name=None):
    assert len(datafiles_ids) > 0

    # Fetch the object from the database
    creator = get_user(creator_id)

    dataset = get_entry(dataset_id)

    datafiles = db.session.query(DataFile) \
        .filter(DataFile.id.in_(datafiles_ids)).all()

    latest_dataset_version = get_latest_dataset_version(dataset_id)
    if latest_dataset_version:
        version = latest_dataset_version.version + 1
    else:
        version = 1

    # If we did not set a name for the dataset_version, we take one by default
    if not name:
        name = "".join([dataset.name, "_v", str(version)])

    # Create the DatasetVersion object
    new_dataset_version = DatasetVersion(name=name,
                                         creator=creator,
                                         dataset=dataset,
                                         datafiles=datafiles,
                                         version=version)

    db.session.add(new_dataset_version)
    db.session.commit()

    return new_dataset_version


def get_dataset_version(dataset_version_id=0):
    dataset_version = db.session.query(DatasetVersion) \
        .filter(DatasetVersion.id == dataset_version_id) \
        .one()

    return dataset_version


def get_dataset_versions(dataset_id=0):
    dataset_versions = db.session.query(DatasetVersion) \
        .filter(DatasetVersion.dataset_id == dataset_id) \
        .all()

    return dataset_versions


def get_dataset_version_provenance(dataset_version_id=0,
                                   provenance=None):
    # TODO: See how to manage the provenance
    raise NotImplementedError


def get_latest_dataset_version_by_permaname(permaname):
    dataset_version = db.session.query(DatasetVersion) \
        .filter(Dataset.permaname == permaname) \
        .order_by(DatasetVersion.version.desc()) \
        .one()

    return dataset_version

def get_dataset_version_by_permaname_and_version(permaname,
                                                 version):
    """From the permaname of a dataset, retrieve the specific dataset version"""
    # dataset = get_dataset_from_permaname(permaname)
    dataset_version = db.session.query(DatasetVersion) \
        .filter(DatasetVersion.version == version) \
        .filter(Dataset.permaname == permaname) \
        .one()

    return dataset_version


def get_dataset_version_by_dataset_id_and_dataset_version_id(dataset_id,
                                                             dataset_version_id):
    dataset_version = get_dataset_version(dataset_version_id)
    return dataset_version


# </editor-fold>

# <editor-fold desc="Entry">
def get_entry(entry_id):
    entry = db.session.query(Entry) \
        .filter(Entry.id == entry_id) \
        .one()

    return entry


# TODO: I don't think we need this anymore
# def _convert_entries_to_dict(entries):
# </editor-fold>

# <editor-fold desc="DataFile">
def add_datafile(s3_bucket,
                 s3_key,
                 name="No name",
                 url="",
                 type=DataFile.DataFileType.Raw):
    # TODO: See register_datafile_id
    new_datafile_name = name

    new_datafile_url = url

    new_datafile = DataFile(name=new_datafile_name,
                            s3_bucket=s3_bucket,
                            s3_key=s3_key,
                            url=new_datafile_url,
                            type=type)

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


# </editor-fold>

# <editor-fold desc="Upload Session">
def add_new_upload_session(user_id):
    # TODO: Remove the default user once we have the auth in place
    # us = UploadSession(user_id=user_id)
    us = UploadSession(user_id=_get_test_user().id)
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
    Upload = 'upload/'
    Convert = 'convert/'
    Export = 'export/'


def generate_convert_key():
    enumed_convert_path = EnumS3FolderPath.Convert.value
    return os.path.join(enumed_convert_path + str(uuid.uuid4()))


def add_upload_session_file(session_id, filename, filetype, url, s3_bucket):
    enumed_filetype = DataFile.DataFileType(filetype)

    converted_s3_key = generate_convert_key()

    upload_session_file = UploadSessionFile(session_id=session_id,
                                            filename=filename,
                                            initial_filetype=enumed_filetype,
                                            url=url,
                                            converted_s3_bucket=s3_bucket,
                                            converted_s3_key=converted_s3_key)
    db.session.add(upload_session_file)
    db.session.commit()
    return upload_session_file


def get_upload_session_file(upload_session_file_id):
    upload_session_file = db.session.query(UploadSessionFile) \
        .filter(UploadSessionFile.id == upload_session_file_id).one()
    return upload_session_file


def update_session_file_converted_type(converted_type, upload_session_file_id):
    upload_session_file = get_upload_session_file(upload_session_file_id)
    upload_session_file.converted_filetype = converted_type

    db.session.add(upload_session_file)
    db.session.commit()

    return upload_session_file


# </editor-fold>

# <editor-fold desc="Download datafiles">


# def get_dataset(dataset_id):
#     dataset = db.session.query(Dataset) \
#         .filter(Dataset.id == dataset_id).one()
#
#     return dataset
#
#
# def get_dataset_from_permaname(dataset_permaname):
#     dataset = db.session.query(Dataset) \
#         .filter(Dataset.permaname == dataset_permaname) \
#         .one()
#
#     return dataset
#
# def resolve_to_dataset(name):
#     m = re.match("([^/:]+)$", name)
#     if m is None:
#         return None
#     permaname_or_id = m.group(1)
#
#     dataset = get_dataset(permaname_or_id)
#     if dataset is None:
#         dataset_version = get_dataset_version_by_id(permaname_or_id)
#         if dataset_version is None:
#             return None
#         dataset = dataset_version.dataset
#
#     return dataset
#
# def resolve_to_dataset_version(name):
#     m = re.match("([^/:]+)(?::([0-9]+))?$", name)
#     if m is None:
#         return None
#     permaname = m.group(1)
#     version = m.group(2)
#
#     dataset_id = resolve_to_dataset(permaname)
#     if dataset_id is None:
#         if get_dataset_version(permaname) is not None:
#             return permaname
#         else:
#             return None
#
#     dataset = get_dataset(dataset_id)
#     # now look for version
#     if version == "" or version is None:
#         version = len(dataset['versions'])-1
#     else:
#         version = int(version)-1
#
#     if version >= len(dataset['versions']):
#         return None
#
#     dataset_version_id = dataset['versions'][version]
#     return dataset_version_id
#
# import re
# def resolve_to_datafile(name):
#     m = re.match("([^/:]+(?::[0-9]+)?)(/.*)$", name)
#     if m is None:
#         return None
#     dataset_name = m.group(1)
#     path = m.group(2)
#
#     dataset_version_id = resolve_to_dataset_version(dataset_name)
#     if dataset_version_id is None:
#         return None
#
#     dataset_version = get_dataset_version(dataset_version_id)
#     if path == "":
#         path = dataset_version["entries"]["name"]
#
#     entries = [e for e in dataset_version['entries'] if e['name'] == path]
#     if len(entries) == 0:
#         return None
#     else:
#         return entries[0]

def _find_cache_entry(dataset_version_id, format, datafile_name):
    entry = db.session.query(ConversionCache).filter(and_(ConversionCache.dataset_version_id == dataset_version_id,
                                                          ConversionCache.format == format,
                                                          ConversionCache.datafile_name == datafile_name)).first()
    return entry


def get_signed_urls_from_cache_entry(paths_as_json):
    # if there's urls on the cache entry, report those too after signing them
    if paths_as_json is None or paths_as_json == "":
        return None

    urls = json.loads(paths_as_json)
    signed_urls = [aws.sign_url(url) for url in urls]
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
                                status=status)
        db.session.add(entry)
        db.session.commit()

    assert entry.id is not None
    return is_new, entry


def update_conversion_cache_entry(entry_id, status, urls=None):
    print("update_conversion_cache", entry_id, status, urls)
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
        update({"task_id":task_id})
    db.session.commit()

def delete_conversion_cache_entry(entry_id):
    db.session.query(ConversionCache). \
        filter(ConversionCache.id == entry_id). \
        delete()
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
            dataset_version = get_latest_dataset_version_by_permaname(dataset_permaname)
        else:
            dataset_version = get_dataset_version_by_permaname_and_version(dataset_permaname, version_number)

        if dataset_version is None:
            return None

        dataset_version_id = dataset_version.id
    else:
        if dataset_version_id is None:
            raise IllegalArgumentError("Must have either a permaname or a dataset_version_id")
        if version_number is not None:
            raise IllegalArgumentError("If permaname is not provided, cannot use version number in search")

    if datafile_name is None:
        dataset_version = get_dataset_version(dataset_version_id)
        if len(dataset_version.datafiles) > 1:
            raise IllegalArgumentError("The retrieved dataset version has more than one datafile so the name must be specified")
        else:
            datafile = list(dataset_version.datafiles)[0]
    else:
        datafile = get_datafile_by_version_and_name(dataset_version_id, datafile_name)

    return datafile

#</editor-fold>
