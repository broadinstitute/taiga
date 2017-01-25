from taiga2.backend import backend_app, create_db
from taiga2.controllers.models_controller import *

# Create the Admin user
# Create the origin data in Home folder
# Create Folder A
# Create Folder B inside Folder A
# Create Data inside Folder B
# Create A1 Data/A2 Data/A3 Data inside Folder A

if __name__ == "__main__":
    with backend_app.app_context():
        print("Dropping existing DB")
        db.drop_all()
        print("Recreating it")
        create_db()

        # Create the Admin user
        admin_user = add_user(name="Admin")
        home_folder_admin = admin_user.home_folder

        # Create a session where all this is happening
        upload_session = add_new_upload_session()

        # Create the origin data
        upload_session_file_origin = add_upload_session_file(upload_session.id, "origin")
        origin_dataset = add_dataset(name="origin",
                                     creator_id=admin_user.id)

        # Create a DataFile for the origin dataset
        datafile_origin_dataset = add_datafile(name="Origin Datafile",
                                               upload_session_file_id=upload_session_file_origin.id)

        # Create a dataVersion to origin
        origin_first_datasetVersion = add_dataset_version(creator_id=admin_user.id,
                                                          dataset_id=origin_dataset.id,
                                                          datafiles_ids=[datafile_origin_dataset.id])
        # Add the origin dataset inside the home folder
        add_folder_entry(folder_id=home_folder_admin.id,
                         entry_id=origin_dataset.id)

        # Create the Folder A folder
        folderA = add_folder(creator_id=admin_user.id,
                             name="Folder A",
                             folder_type=Folder.FolderType.folder)
        add_folder_entry(folder_id=home_folder_admin.id,
                         entry_id=folderA.id)

        # Create Folder B inside Folder A
        folderB = add_folder(creator_id=admin_user.id,
                             name="Folder B",
                             folder_type=Folder.FolderType.folder)
        add_folder_entry(folder_id=folderA.id,
                         entry_id=folderB.id)

        # Create Data inside Folder B
        upload_session_file_data = add_upload_session_file(upload_session.id, "Data")
        data = add_dataset(name="Data",
                           creator_id=admin_user.id)

        dataset_version_data = add_dataset_version(creator_id=admin_user.id,
                                                   dataset_id=data.id)

        add_folder_entry(folder_id=folderB.id,
                         entry_id=dataset_version_data.id)

        add_folder_entry(folder_id=folderB.id,
                         entry_id=data.id)

        # Create A1 Data/A2 Data/A3 Data inside Folder A
        for i in range(1, 4):
            name = "".join(['A', str(i), " DatasetVersion"])
            dataAX = add_dataset_version(name=name,
                                         creator_id=admin_user.id,
                                         dataset_id=origin_dataset.id)
            add_folder_entry(folder_id=folderA.id,
                             entry_id=dataAX.id)
