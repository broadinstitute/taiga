from taiga2.app import *
from taiga2.models import *
from taiga2.schemas import *

if __name__ == "__main__":
    with frontend_app.app_context():
        folder_schema = FolderSchema()
        folderA = db.session.query(Folder).filter(Folder.name == "Home").one()
        print("Home: {}".format(folderA))
        data_folder_a = folder_schema.dump(folderA).data
        print("")
        print("Data of Home: {}".format(data_folder_a))

        user_schema = UserSchema()
        admin = db.session.query(User).filter(User.name == "Admin").one()
        data_admin_user = user_schema.dump(admin).data
        print("")
        print("Data of Admin user: {}".format(data_admin_user))

        dataset_schema = DatasetSchema()
        dataset_origin = db.session.query(Dataset).filter(Dataset.name == "origin").one()
        data_dataset_origin = dataset_schema.dump(dataset_origin).data
        print("")
        print("Data of Dataset first: {}".format(data_dataset_origin))