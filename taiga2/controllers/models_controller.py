from taiga2.models import User, Folder, Entry, Dataset

from taiga2.models import db

# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)


# ------- User -------
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


# ------ Folder --------
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


# We don't need add_folder_entry thanks to SQLAlchemy
def add_folder_entry(folder_id, entry_id):
    folder = get_folder(folder_id)
    entry = get_entry(entry_id)

    folder.entries.append(entry)

    return folder


# We don't need remove_folder_entry thanks to SQLAlchemy
def remove_folder_entry(folder_id, entry_id):
    folder = get_folder(folder_id)
    entry = get_entry(entry_id)

    folder.entries.remove(entry)

    return folder


# TODO: Populate this function?
def get_folders_containing():
    raise NotImplementedError


def get_parent_folders(entry_id):
    entry = db.session.query(Entry) \
            .filter(Entry.id == entry_id).one()
    parent_folders = entry.folders

    return parent_folders


# ------ Dataset --------
def add_dataset(name="No name",
                permaname=None,
                description="No description provided"):
    new_dataset = Dataset(name=name,
                          permaname=permaname,
                          description=description)

    db.session.add(new_dataset)
    db.session.commit()

    return new_dataset


# ------ Entry --------
def get_entry(entry_id):
    entry = db.session.query(Entry) \
        .filter(Entry.id == entry_id) \
        .one()

    return entry


# TODO: I don't think we need this anymore
# def _convert_entries_to_dict(entries):


# ------ Datafile --------
def add_datafile():
    # TODO: See register_datafile_id
    raise NotImplementedError

