import argparse
import csv
import flask

from urllib.parse import urlparse
from sqlalchemy.orm.exc import NoResultFound

from taiga2.api_app import create_app, create_db
from taiga2.controllers import models_controller


class DataFileInfo:
    def __init__(self, id, datafile, owner_email, version=None, creation_date=None):
        self.id = id
        self.datafile = datafile
        self.owner_email = owner_email
        self.version = version
        self.creation_date = creation_date


class DatasetVersionFileInfo:
    def __init__(self):
        self.datafiles_info = []


def populate_db(dataset_csv_path, dataset_version_with_datafile_csv_path):
    # TODO: We should handle the Public folder properly, instead of adding it to Philip's account
    # Summary
    nb_user_created = 0
    nb_user_skipped = 0
    nb_dataset_created = 0
    nb_row_dataset_skipped = 0
    nb_datafile_created = 0
    nb_datafile_skipped = 0
    nb_row_datafile_skipped = 0
    nb_dataset_version_created = 0
    nb_dataset_version_skipped = 0


    # Dictionary to link find the dataset matching the dataset via the permanames to create the dataset versions
    # Dict<String, Array<int>>
    dict_permaname_datafile_ids = {}

    # We first manage the dataset creation
    with open(dataset_csv_path) as dataset_file:
        print("Creating the users and the datasets")
        reader = csv.DictReader(dataset_file)

        for row in reader:
            is_public = False

            if not row["permaname"]:
                print("Warning: We found an empty permaname entry: {}. Skipping it.".format(row))
                nb_row_dataset_skipped += 1
                continue

            dataset_name = row["name"]
            dataset_permaname = row["permaname"]
            dataset_description = row["description"]

            if row["folder"].startswith("home"):
                dataset_folder_user = row["folder"]

                # To get the user from dataset_folder_user, we extract the user from the parenthesis
                dataset_user_email = dataset_folder_user[
                                     dataset_folder_user.find("(") + 1:dataset_folder_user.find(")")]

                # Handle the case where user email is None
                if dataset_user_email == "None":
                    print("Warning: We found a row with folder {}. Skipping it.".format(row["folder"]))
                    nb_user_skipped += 1
                    continue

                # To get the target folder, we take the string before the parenthesis
                dataset_folder_name = dataset_folder_user.split("(")[0]
            else:
                # For now, we store all the others into pmontgomery@broadinstitute.org
                is_public = True
                dataset_folder_name = row["folder"]
                dataset_user_email = "pmontgom@broadinstitute.org"

            # Setting up the user
            try:
                dataset_current_user = models_controller.get_user_by_email(dataset_user_email)
            except NoResultFound:
                # User does not exists yet, so we create it
                dataset_user_name = dataset_user_email[:dataset_user_email.find("@")]
                dataset_current_user = models_controller.add_user(name=dataset_user_name,
                                                                  email=dataset_user_email)
                print("User with email: {} created".format(dataset_user_email))
                nb_user_created += 1

            flask.g.current_user = dataset_current_user

            # TODO: We should not create the dataset if it already exists
            new_dataset = models_controller.add_dataset(name=dataset_name,
                                                        permaname=dataset_permaname,
                                                        description=dataset_description)
            try:
                # TODO: Check it is case insensitive
                if str.lower(dataset_folder_name) == "home":
                    dataset_folder = dataset_current_user.home_folder
                elif str.lower(dataset_folder_name) == "trash":
                    dataset_folder = dataset_current_user.trash_folder
                else:
                    dataset_folder = models_controller.get_folder_by_name(dataset_folder_name)
            except NoResultFound:
                # If no result, it means we need to create the folder in the user space or in public
                dataset_folder = models_controller.add_folder(name=dataset_folder_name,
                                                              folder_type=models_controller.Folder.FolderType.folder,
                                                              description=None)

                if is_public:
                    models_controller.move_to_folder(entry_ids=[dataset_folder.id],
                                                     current_folder_id=None,
                                                     target_folder_id=models_controller.get_public_folder().id)
                else:
                    models_controller.move_to_folder(entry_ids=[dataset_folder.id],
                                                     current_folder_id=None,
                                                     target_folder_id=dataset_current_user.home_folder_id)

            # Now we can move the dataset to the folder
            models_controller.move_to_folder([new_dataset.id], None, dataset_folder.id)

            # We add the dataset_permaname as key with value an empty array so we can add each matching datafile
            dict_permaname_datafile_ids[dataset_permaname] = []

            nb_dataset_created += 1

    # We then manage the attribution of the dataset_version to the freshly created datasets
    with open(dataset_version_with_datafile_csv_path) as dataset_version_with_datafile_csv:
        print("")
        print("Creating the datafiles")
        reader = csv.DictReader(dataset_version_with_datafile_csv)

        for row in reader:
            if not row["permaname"]:
                print("We found an empty permaname entry: {}. Skipping it.".format(row))
                nb_row_datafile_skipped += 1
                nb_datafile_skipped += 1
                continue

            # We first create the datafiles
            datafile_type = row["type"]
            datafile_name = row.get("name", "data")
            datafile_s3_location = urlparse(row["s3_location"])
            datafile_short_summary = row["short_desc"]
            datafile_long_summary = row.get("long_desc", "")
            datafile_id = row["id"]
            datafile_creation_date = row["created_timestamp"]
            datafile_version = row["version"]
            datafile_created_by = row["created_by"]

            dataset_permaname = row["permaname"]

            # s3://taiga2/imported/4bb2169e-5b87-4d1c-a78e-3e6006316561.hdf5
            datafile_s3_bucket = datafile_s3_location.netloc
            datafile_s3_key = datafile_s3_location.path[1:]  # We remove the first '/'

            # Set the user to the one in the row to make the manipulations under his name
            try:
                current_user = models_controller.get_user_by_email(datafile_created_by)
            except NoResultFound:
                print("Warning: The user email found in 'created_by' column ({}) was not found in the dataset side. "
                      "Creating one."
                      .format(datafile_created_by))
                datafile_created_by_name = datafile_created_by[:datafile_created_by.find("@")]
                current_user = models_controller.add_user(name=datafile_created_by_name,
                                                          email=datafile_created_by)
                nb_user_created += 1

            flask.g.current_user = current_user

            # TODO: We should not create the datafile if it already exists: ie s3_bucket/s3_key exists
            new_datafile = models_controller.add_s3_datafile(s3_bucket=datafile_s3_bucket,
                                                          s3_key=datafile_s3_key,
                                                          name=datafile_name,
                                                          type=datafile_type,
                                                          short_summary=datafile_short_summary,
                                                          long_summary=datafile_long_summary)

            # We register the datafile with its permaname dataset to later create the dataset version
            # with all the datafiles
            if dataset_permaname in dict_permaname_datafile_ids:
                datafile_info = DataFileInfo(id=datafile_id,
                                             datafile=new_datafile,
                                             version=datafile_version,
                                             creation_date=datafile_creation_date,
                                             owner_email=datafile_created_by)
                dict_permaname_datafile_ids[dataset_permaname].append(datafile_info)
            else:
                print("Warning: We found a dataset ({}) without a matching dataset ({}). Skipping it." \
                      .format(datafile_id, dataset_permaname))
                nb_datafile_skipped += 1
                continue

            nb_datafile_created += 1

    # Then we create the dataset_version with the taiga id, linking with the dataset using its permaname
    print("")
    print("Linking the datafiles with the datasets")
    for dataset_permaname, array_data_file_info in dict_permaname_datafile_ids.items():
        dataset = models_controller.get_dataset_from_permaname(dataset_permaname)

        # Get the creation date from the first dataset_version
        for datafile_info in array_data_file_info:
            flask.g.current_user = models_controller.get_user_by_email(datafile_info.owner_email)
            # TODO: We should not create the dataset_version if it already exists. ie version already exists for this dataset
            dataset_version = models_controller.add_dataset_version(dataset_id=dataset.id,
                                                                    datafiles_ids=[datafile_info.datafile.id],
                                                                    anterior_creation_date=datafile_info.creation_date,
                                                                    forced_id=datafile_info.id)

            # Then we edit the dataset version creation_date to the
            if int(datafile_info.version) == 1:
                models_controller.update_dataset_creation_date(dataset_id=dataset.id,
                                                               new_date=datafile_info.creation_date)

        nb_dataset_version_created += 1

    print("")
    print("Done! Here is the summary:")
    print("\tLines skipped in dataset file: {}".format(nb_row_dataset_skipped))
    print("\tLines skipped in datafile file: {}".format(nb_row_datafile_skipped))
    print("")
    print("\tDatasets created: {}".format(nb_dataset_created))
    print("\tUsers created: {}".format(nb_user_created))
    print("\tUsers skipped: {}".format(nb_user_skipped))
    print("")
    print("\tDatafiles created: {}".format(nb_datafile_created))
    print("\tDatafiles skipped: {}".format(nb_datafile_skipped))
    print("")
    print("\tDatasetVersions created: {}".format(nb_dataset_version_created))
    print("\tDatasetVersions skipped and datasets cleaned: {}".format(nb_dataset_version_skipped))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--settings", required=True,
                        help="Settings used for the creation of the api/backends apps")
    parser.add_argument("-d", "--dataset", required=True, help="Dataset csv file path")
    parser.add_argument("-dv", "--dataset_version", required=True, help="Dataset version with datafile csv file path")

    args = parser.parse_args()

    settings_path = args.settings
    dataset_csv_path = args.dataset
    dataset_version_with_datafile_csv_path = args.dataset_version

    print("Dataset path: {}".format(dataset_csv_path))
    print("Dataset version path: {}".format(dataset_version_with_datafile_csv_path))

    api_app, backend_app = create_app(settings_file=settings_path)

    with backend_app.app_context():
        # Use the next line only when you are sure you want to drop the db
        # models_controller.db.drop_all()
        # models_controller.db.create_all()
        populate_db(dataset_csv_path, dataset_version_with_datafile_csv_path)
