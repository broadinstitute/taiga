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


def populate_db(dataset_version_with_datafile_csv_path):
    with open(dataset_version_with_datafile_csv_path) as dataset_version_file:
        print("Fixing the description and version of the dataset versions:")
        reader = csv.DictReader(dataset_version_file)

        for row in reader:
            dataset_permaname = row["permaname"]
            dataset_version_id = row["dataset_id"]
            dataset_version_version = row["version"]
            dataset_version_description = row["description"]

            try:
                dataset = models_controller.get_dataset_from_permaname(dataset_permaname)
            except NoResultFound:
                print("Dataset {} was not found in db".format(dataset_permaname))

            for from_dataset_dataset_versions in dataset.dataset_versions:
                if dataset_version_id == from_dataset_dataset_versions.id:
                    if from_dataset_dataset_versions.description != dataset_version_description:
                        print("Dataset {} => In Db: {}, in csv: '{}'".format(dataset.permaname,
                                                                             from_dataset_dataset_versions.description,
                                                                             dataset_version_description))
                        models_controller.update_dataset_version_description(dataset_version_id=dataset_version_id,
                                                                             new_description=dataset_version_description)
                    if int(dataset_version_version) != from_dataset_dataset_versions.version:
                        print("Dataset version => In Db: {}, in csv: {}".format(from_dataset_dataset_versions.version,
                                                                                dataset_version_version))
                        from_dataset_dataset_versions.version = int(dataset_version_version)
                        models_controller.db.session.add(from_dataset_dataset_versions)
                        models_controller.db.session.commit()
                        print("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--settings", required=True,
                        help="Settings used for the creation of the api/backends apps")
    parser.add_argument("-dv", "--dataset_version", required=True, help="Dataset version with datafile csv file path")

    args = parser.parse_args()

    settings_path = args.settings
    dataset_version_with_datafile_csv_path = args.dataset_version

    print("Dataset version path: {}".format(dataset_version_with_datafile_csv_path))

    api_app, backend_app = create_app(settings_file=settings_path)

    with backend_app.app_context():
        # Use the next line only when you are sure you want to drop the db
        # models_controller.db.drop_all()
        # models_controller.db.create_all()
        populate_db(dataset_version_with_datafile_csv_path)
