from taiga2.app import *
from taiga2.models import *
from taiga2.schemas import *

if __name__ == "__main__":
    with frontend_app.app_context():
        # Test Folder Schema
        folder_schema = FolderSchema()
        folderA = db.session.query(Folder).filter(Folder.name == "Home").one()
        print("Home: {}".format(folderA))
        data_folder_a = folder_schema.dump(folderA).data
        print("")
        print("Data of Home: {}".format(data_folder_a))

        # Test User Schema
        user_schema = UserSchema()
        admin = db.session.query(User).filter(User.name == "Admin").one()
        data_admin_user = user_schema.dump(admin).data
        print("")
        print("Data of Admin user: {}".format(data_admin_user))

        # Test Dataset Schema
        dataset_schema = DatasetSchema()
        dataset_origin = db.session.query(Dataset).filter(Dataset.name == "origin").one()
        data_dataset_origin = dataset_schema.dump(dataset_origin).data
        print("")
        print("Data of Dataset first: {}".format(data_dataset_origin))

        # Test Datafile Schema
        datafile_schema = DataFileSummarySchema()
        datafile_origin = db.session.query(DataFile).filter(DataFile.name == "Origin Datafile").one()
        data_datafile_origin = datafile_schema.dump(datafile_origin).data
        print("")
        print("Data of DataFile Origin: {}".format(data_datafile_origin))

        # Test DatasetVersion Schema
        dataset_version_schema = DatasetVersionSchema()
        dataset_version_origin = db.session.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_origin.id).first()
        data_dataset_version_origin = dataset_version_schema.dump(dataset_version_origin).data
        print("")
        print("Data of DatasetVersion origin first: {}".format(data_dataset_version_origin))