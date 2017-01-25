from taiga2.models import *
from taiga2.models import generate_permaname
from taiga2.models import db

from sqlalchemy.sql.expression import func

# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)

# IMPORTANT:
#   If you have this error "RuntimeError: application not registered on db instance and
#   no application bound to current context" while trying around within command line,
#   You need to push the context of you app => app.app_context().push() (for us frontend_app.app_context().push()

#<editor-fold desc="User">
def add_user(name):
    new_user = User(name=name)

    home_folder = Folder(name="Home",
                         folder_type=Folder.FolderType.home,
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


def get_user(user_id):
    return db.session.query(User).filter(User.id == user_id).first()
#</editor-fold>

#<editor-fold desc="Folder">
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
    # If it is a dataset, we need to update the location of its dataset_versions
    if type(entry) is Dataset:
        # Add this folder to the dataset_versions
        for dataset_version in entry.dataset_versions:
            add_folder_entry(folder_id, dataset_version.id)

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
#</editor-fold>

#<editor-fold desc="Dataset">
def add_dataset(name="No name",
                creator_id=None,
                permaname=None,
                description="No description provided",
                datafiles_ids=None):
    if not permaname:
        permaname = generate_permaname(name)

    creator = get_user(creator_id)
    new_dataset = Dataset(name=name,
                          permaname=permaname,
                          description=description,
                          creator=creator)

    db.session.add(new_dataset)
    db.session.commit()

    if datafiles_ids:
        # It means we would want to create a first dataset with a DatasetVersion
        # containing DataFiles

        # TODO: Think about a meaningful name
        new_dataset_version = add_dataset_version(creator_id=creator.id,
                                                  dataset_id=new_dataset.id,
                                                  version=1,
                                                  datafiles_ids=datafiles_ids)

        db.session.add(new_dataset_version)
        db.session.commit()

    # Add the related activity
    # TODO: Add the activity
    # TODO: Think about an automatic way of adding/updating the activity
    return new_dataset


def get_dataset(dataset_id):
    dataset = db.session.query(Dataset) \
        .filter(Dataset.id == dataset_id).one()

    return dataset


def get_dataset_from_permaname(dataset_permaname):
    dataset = db.session.query(Dataset) \
        .filter(Dataset.permaname == dataset_permaname) \
        .one()

    return dataset


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
#def update_datafile_summaries


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
                                                                     for datafile in dataset_version_latest_version.datafiles],
                                                      version=dataset_version_latest_version.version+1)

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


#</editor-fold>

#<editor-fold desc="DatasetVersion">
def add_dataset_version(creator_id,
                        dataset_id,
                        datafiles_ids=None,
                        version=1,
                        name=None):
    if not datafiles_ids:
        datafiles_ids = []

    # Fetch the object from the database
    creator = get_user(creator_id)

    dataset = get_entry(dataset_id)

    # TODO: User the power of Query to make only one query instead of calling get_datafile
    datafiles = [get_datafile(datafile_id) for datafile_id in datafiles_ids]

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


def get_dataset_version_provenance(dataset_version_id=0,
                                   provenance=None):
    # TODO: See how to manage the provenance
    raise NotImplementedError


def get_dataset_version_by_permaname_and_version(permaname,
                                                 version):
    """From the permaname of a dataset, retrieve the specific dataset version"""
    # dataset = get_dataset_from_permaname(permaname)
    dataset_version = db.session.query(DatasetVersion) \
        .filter(DatasetVersion.version == version) \
        .filter(Dataset.permaname == permaname) \
        .one()

    return dataset_version

#</editor-fold>

#<editor-fold desc="Entry">
def get_entry(entry_id):
    entry = db.session.query(Entry) \
        .filter(Entry.id == entry_id) \
        .one()

    return entry


# TODO: I don't think we need this anymore
# def _convert_entries_to_dict(entries):
#</editor-fold>

#<editor-fold desc="DataFile">
def add_datafile(name="No name",
                 permaname=None,
                 url="",
                 upload_session_file_id=-1):
    # TODO: See register_datafile_id
    new_datafile_name = name
    if not permaname:
        new_datafile_permaname = generate_permaname(new_datafile_name)
    else:
        new_datafile_permaname = permaname

    new_datafile_url = url

    upload_session_file = get_upload_session_file(upload_session_file_id)

    new_datafile = DataFile(name=new_datafile_name,
                            permaname=new_datafile_permaname,
                            url=new_datafile_url,
                            upload_session_file=upload_session_file)

    db.session.add(new_datafile)
    db.session.commit()

    return new_datafile


def get_datafile(datafile_id):
    datafile = db.session.query(DataFile) \
        .filter(DataFile.id == datafile_id).one()

    return datafile
#</editor-fold>

#<editor-fold desc="Upload Session">
def add_new_upload_session():
    us = UploadSession()
    db.session.add(us)
    db.session.commit()
    return us


def get_upload_session(session_id):
    upload_session = db.session.query(UploadSession).filter(UploadSession.id == session_id).one()
    return upload_session


def get_datafiles_from_session(session_id):
    # TODO: We could also fetch the datafiles with only one query
    upload_session = db.session.query(UploadSession) \
        .filter(UploadSession.id == session_id).one()
    upload_session_files = upload_session.upload_session_files

    # For each upload_session_file, we retrieve its datafile
    datafiles = []
    for upload_session_file in upload_session_files:
        datafiles.append(upload_session_file.datafile)
    print("Retrieved datafiles from upload_session files {} are {}".format(upload_session_files, datafiles))
    return datafiles

#</editor-fold>

#<editor-fold desc="Upload Session File">
def add_upload_session_file(session_id, filename):
    upload_session_file = UploadSessionFile(session_id=session_id,
                                            filename=filename)
    db.session.add(upload_session_file)
    db.session.commit()
    return upload_session_file

def get_upload_session_file(upload_session_file_id):
    upload_session_file = db.session.query(UploadSessionFile) \
        .filter(UploadSessionFile.id == upload_session_file_id).one()
    return upload_session_file
#</editor-fold>
