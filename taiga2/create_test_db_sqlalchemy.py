from taiga2.app import frontend_app, create_db
from taiga2.controllers.models_controller import *

# Create the Admin user
# Create the origin data in Home folder
# Create Folder A
# Create Folder B inside Folder A
# Create Data inside Folder B
# Create A1 Data/A2 Data/A3 Data inside Folder A

if __name__ == "__main__":
    with frontend_app.app_context():
        print("Dropping existing DB")
        db.drop_all()
        print("Recreating it")
        create_db()

        # Create the Admin user
        admin_user = add_user(name="Admin")
        home_folder_admin = admin_user.home_folder

        # Create the origin data
        origin_dataset = add_dataset(name="origin",
                                     creator_id=admin_user.id)
        # Create a dataVersion to origin
        origin_first_datasetVersion = add_dataset_version(name="origin_v1",
                                                          creator_id=admin_user.id,
                                                          dataset_id=origin_dataset.id)
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
        data = add_dataset(name="Data",
                           creator_id=admin_user.id)
        add_folder_entry(folder_id=folderB.id,
                         entry_id=folderB.id)

        # Create A1 Data/A2 Data/A3 Data inside Folder A
        for i in range(1, 4):
            name = "".join(['A', str(i), " Data"])
            dataAX = add_dataset(name=name,
                                 creator_id=admin_user.id)
            add_folder_entry(folder_id=folderA.id,
                             entry_id=dataAX.id)
