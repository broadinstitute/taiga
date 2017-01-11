from taiga2.models import User, Folder
from taiga2.controllers.models_controller import  add_user


def test_user(session):
    new_user_name = "User_Test"
    new_user = User(name=new_user_name)

    home_folder = Folder(name="Home",
                         folder_type=Folder.FolderType.home,
                         creator=new_user)

    trash_folder = Folder(name="Trash",
                          folder_type=Folder.FolderType.trash,
                          creator=new_user)

    session.add(home_folder)
    session.add(trash_folder)
    session.add(new_user)

    session.flush()

    new_user.home_folder = home_folder
    new_user.trash_folder = trash_folder

    assert new_user.id == 1
    assert new_user.name == new_user_name
    assert new_user.home_folder.name == "Home"


def test_add_user(session):
    add_user(name="Remi")

    assert session.query(User).filter(User.name == "Remi").first().name == "Remi"
