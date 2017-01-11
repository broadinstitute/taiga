from taiga2.models import User, Folder
from taiga2.models import db
from flask import current_app

# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)
# STOP delete

## from taiga2.controllers.models_controller import *

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
