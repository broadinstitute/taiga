import logging
import readline
import sys

from taiga2.api_app import create_app, create_db
from taiga2.controllers.models_controller import *

log = logging.getLogger(__name__)

# Create the Admin user
# Create the origin data in Home folder
# Create Folder A
# Create Folder B inside Folder A
# Create Data inside Folder B
# Create A1 Data/A2 Data/A3 Data inside Folder A

## NEVER USE IN PRODUCTION


def drop_and_create_db():
    db.drop_all()
    print("Recreating it")
    create_db()

    # Create the Admin user
    admin_user = add_user(name="Admin")
    home_folder_admin = admin_user.home_folder

    # Create a session where all this is happening
    upload_session_origin = add_new_upload_session()

    # Create the origin data
    upload_session_file_origin = add_upload_session_file(upload_session_origin.id,
                                                         "origin",
                                                         DataFile.DataFileType.Raw,
                                                         "www.origin_url.com")
    origin_dataset = add_dataset_from_session(session_id=upload_session_origin.id,
                                              dataset_name="origin",
                                              dataset_description="No description",
                                              current_folder_id=home_folder_admin.id)

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
    upload_session_data = add_new_upload_session()
    upload_session_file_data = add_upload_session_file(upload_session_data.id,
                                                       "Data",
                                                       DataFile.DataFileType.Raw,
                                                       "www.data.com")

    data = add_dataset_from_session(session_id=upload_session_data.id,
                                    dataset_name="Data",
                                    dataset_description="No description",
                                    current_folder_id=folderB.id)

    # Create A1 Data/A2 Data/A3 Data inside Folder A
    for i in range(1, 4):
        name = "".join(['A', str(i), " DatasetVersion"])
        dataAX = add_dataset_version(name=name,
                                     creator_id=admin_user.id,
                                     dataset_id=origin_dataset.id)
        add_folder_entry(folder_id=folderA.id,
                         entry_id=dataAX.id)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        log.error("Needs config file")
        sys.exit(-1)

    settings_file = sys.argv[1]

    api_app, backend_app = create_app(settings_file=settings_file)

    with backend_app.app_context():
        print("Dropping existing DB")

        sure = input("WAIT! Dropping DB...are you sure? ")
        if sure == 'y':
            sure_sure = input("Really sure?? ")
            if sure_sure != 'yes':
                if sure_sure.lower() == 'y' or sure_sure.lower() == 'yes':
                    print('Nice try but...nope!')
                else:
                    print("Pfiou...almost a catastrophic event :)")
            else:
                drop_and_create_db()
        else:
            if sure.lower() == 'yes':
                print('Nice try but...nope!')
            print("Better this way...bye!")


