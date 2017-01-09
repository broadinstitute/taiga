from taiga2.models import *

# TODO: Delete this
from sqlalchemy.orm import sessionmaker
engine = create_engine('sqlite:///taiga2.db', echo=True)
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
# STOP delete

## from taiga2.controllers.models_controller import *

# User


def add_user(name):
    new_user = User(name=name)

    home_folder = Folder(name="Home",
                         folder_type=Folder.FolderType.home,
                         creator=new_user)

    trash_folder = Folder(name="Trash",
                          folder_type=Folder.FolderType.trash,
                          creator=new_user)

    session.add(home_folder)
    session.add(trash_folder)
    session.add(new_user)
    session.commit()

    # TODO: Find a fix to the home_folder and trash_folder issue
    new_user.home_folder = home_folder
    new_user.trash_folder = trash_folder

    session.add(new_user)
    session.commit()


def add_folder(creator=None,
               name="Untitled Folder",
               folder_type=Folder.FolderType.folder,
               description="No description provided"):

    new_folder = Folder(name=name,
                        folder_type=folder_type,
                        description=description,
                        creator=creator)
    session.add(new_folder)
    session.commit()