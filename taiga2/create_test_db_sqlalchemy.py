import copy
import logging
import readline
import sys

from taiga2.api_app import create_app, create_db
import taiga2.controllers.models_controller as models_controller
import taiga2.models as models

import flask

log = logging.getLogger(__name__)


# Create the Admin user
# Create the origin data in Home folder
# Create Folder A
# Create Folder B inside Folder A
# Create Data inside Folder B
# Create A1 Data/A2 Data/A3 Data inside Folder A

## NEVER USE IN PRODUCTION

# TODO: Should use the settings.cfg for the bucket name
bucket_name = "broadtaiga2prototype"

def drop_and_create_db():
    models_controller.db.drop_all()
    print("Recreating it")
    create_db()

    # Create the Admin user
    admin_user = models_controller.add_user(name="admin", email="admin@broadinstitute.org")
    home_folder_admin = admin_user.home_folder

    # Setting up the flask user
    flask.g.current_user = admin_user

    # Create a session where all this is happening
    upload_session_origin = models_controller.add_new_upload_session()

    # Create the origin data
    upload_session_file_origin = models_controller.add_upload_session_file(session_id=upload_session_origin.id,
                                                                           filename="origin",
                                                                           s3_bucket=bucket_name,
                                                                           filetype=models_controller.DataFile.DataFileType.Raw,
                                                                           url="www.origin_url.com")
    models_controller.update_session_file_converted_type(converted_type=models_controller.DataFile.DataFileType.Raw,
                                                         upload_session_file_id=upload_session_file_origin.id)

    origin_dataset = models_controller.add_dataset_from_session(session_id=upload_session_origin.id,
                                                                dataset_name="origin",
                                                                dataset_description="No description",
                                                                current_folder_id=home_folder_admin.id)

    # Create the Folder A folder
    folderA = models_controller.add_folder(name="Folder A",
                                           folder_type=models.Folder.FolderType.folder)
    models_controller.add_folder_entry(folder_id=home_folder_admin.id,
                                       entry_id=folderA.id)

    # Create Folder B inside Folder A
    folderB = models_controller.add_folder(name="Folder B",
                                           folder_type=models.Folder.FolderType.folder)
    models_controller.add_folder_entry(folder_id=folderA.id,
                                       entry_id=folderB.id)

    # Create Data inside Folder B
    upload_session_data = models_controller.add_new_upload_session()
    upload_session_file_data = models_controller.add_upload_session_file(session_id=upload_session_data.id,
                                                                         filename="Data",
                                                                         s3_bucket=bucket_name,
                                                                         filetype=models.DataFile.DataFileType.Raw,
                                                                         url="www.data.com")

    models_controller.update_session_file_converted_type(converted_type=models_controller.DataFile.DataFileType.Raw,
                                                         upload_session_file_id=upload_session_file_data.id)

    data = models_controller.add_dataset_from_session(session_id=upload_session_data.id,
                                                      dataset_name="Data",
                                                      dataset_description="No description",
                                                      current_folder_id=folderB.id)

    data_datafiles = models_controller.get_latest_version_datafiles_from_dataset(data.id)

    temp_data_datafiles = copy.copy(data_datafiles)

    # Create A1 Data/A2 Data/A3 Data inside Folder A
    for i in range(1, 4):
        name = "".join(['A', str(i), " DatasetVersion"])

        # We need now to generate new datafiles
        if i >= 1:
            loop_datafiles = []
            for datafile in temp_data_datafiles:
                loop_datafile = models_controller.add_datafile(name=datafile.name + 'v' + str(i),
                                                               s3_bucket=bucket_name,
                                                               s3_key=models_controller.generate_convert_key(),
                                                               url=datafile.url,
                                                               type=datafile.type)
                loop_datafiles.append(loop_datafile)
            temp_data_datafiles = loop_datafiles
        datafiles_id = [datafile.id for datafile in temp_data_datafiles]
        dataAX = models_controller.add_dataset_version(name=name,
                                                       dataset_id=origin_dataset.id,
                                                       datafiles_ids=datafiles_id)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        log.error("Needs config file")
        sys.exit(-1)

    settings_file = sys.argv[1]

    api_app, backend_app = create_app(settings_file=settings_file)

    with backend_app.app_context():
        print("Dropping existing DB")
        drop_and_create_db()
        # sure = input("WAIT! Dropping DB...are you sure? ")
        # if sure == 'y':
        #     sure_sure = input("Really sure?? ")
        #     if sure_sure != 'yes':
        #         if sure_sure.lower() == 'y' or sure_sure.lower() == 'yes':
        #             print('Nice try but...nope!')
        #         else:
        #             print("Pfiou...almost a catastrophic event :)")
        #     else:
        #         drop_and_create_db()
        # else:
        #     if sure.lower() == 'yes':
        #         print('Nice try but...nope!')
        #     print("Better this way...bye!")
