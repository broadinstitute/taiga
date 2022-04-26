from collections import defaultdict
from typing import Collection, DefaultDict, List, Optional, Tuple, Union
import flask
from typing import List, Tuple
from google.cloud import exceptions as gcs_exceptions

# TODO: Change the app containing db to api_app => current_app
from taiga2.controllers import models_controller
import taiga2.schemas as schemas
from taiga2.models import (
    DatasetMetadataDict,
    DatasetVersion,
    DatasetVersionFiles,
    DatasetVersionMetadataDict,
    UploadDataFile,
    UploadS3DataFile,
    UploadS3DataFileDict,
    UploadVirtualDataFile,
    UploadVirtualDataFileDict,
)

from taiga2.third_party_clients.aws import (
    aws,
    create_signed_get_obj,
    create_s3_url as aws_create_s3_url,
)

import taiga2.third_party_clients.figshare as figshare


def get_dataset(datasetId):
    # TODO: We could receive a datasetId being a permaname. This is not good as our function is not respecting the atomicity. Should handle the usage of a different function if permaname
    # try using ID
    dataset = models_controller.get_dataset(datasetId, one_or_none=True)

    # if that failed, try by permaname
    if dataset is None:
        dataset = models_controller.get_dataset_from_permaname(
            datasetId, one_or_none=True
        )

    if dataset is None:
        flask.abort(404)

    # TODO: We should instead check in the controller, but did not want to repeat
    # Remove folders that are not allowed to be seen
    allowed_dataset = dataset
    allowed_dataset.parents = models_controller.filter_allowed_parents(dataset.parents)
    last_dataset_version = models_controller.get_latest_dataset_version(
        allowed_dataset.id
    )
    allowed_dataset.description = last_dataset_version.description

    # Get the rights of the user over the folder
    right = models_controller.get_rights(dataset.id)
    dataset_schema = schemas.DatasetSchema()
    print("The right is: {}".format(right))
    dataset_schema.context["entry_user_right"] = right
    subscription = models_controller.get_dataset_subscription_for_dataset_and_user(
        dataset.id
    )
    dataset_schema.context["subscription_id"] = (
        subscription.id if subscription is not None else None
    )
    json_dataset_data = dataset_schema.dump(allowed_dataset).data
    return json_dataset_data


# TODO: Use for every DatasetVersionSchema?
def get_dataset_version_schema_json(
    dataset_version: DatasetVersion,
    dataset_version_right: models_controller.EntryRightsEnum,
):
    dataset_version_schema = schemas.DatasetVersionSchema()
    dataset_version_schema.context["entry_user_right"] = dataset_version_right

    if dataset_version.figshare_dataset_version_link is not None:
        try:
            figshare_article_info = figshare.get_article_information(
                dataset_version.figshare_dataset_version_link
            )
            dataset_version_schema.context["figshare"] = figshare_article_info
        except:
            pass

    return dataset_version_schema.dump(dataset_version).data


def _get_dataset_version_metadata(
    dataset_permaname: str, dataset_version: Optional[DatasetVersion]
):
    if dataset_version is None:
        return get_dataset(dataset_permaname)

    return _get_dataset_version_from_dataset(dataset_permaname, dataset_version)


def get_dataset_metadata(
    dataset_id: str, version: Optional[DatasetVersion]
) -> Optional[Union[DatasetMetadataDict, DatasetVersionMetadataDict]]:
    if "." in dataset_id:
        dataset_id, version, _ = models_controller.untangle_dataset_id_with_version(
            dataset_id
        )

    return _get_dataset_version_metadata(dataset_id, version)


def _get_dataset_version_from_dataset(datasetId, datasetVersionId):
    dataset_version = models_controller.get_dataset_version_by_dataset_id_and_dataset_version_id(
        datasetId, datasetVersionId, one_or_none=True
    )

    if dataset_version is None:
        # if we couldn't find a version by dataset_version_id, try permaname and version number.
        version_number = None
        try:
            version_number = int(datasetVersionId)
        except ValueError:
            # TODO: Log the error
            pass

        if version_number is not None:
            dataset_version = models_controller.get_dataset_version_by_permaname_and_version(
                datasetId, version_number, one_or_none=True
            )
        else:
            dataset_version = models_controller.get_latest_dataset_version_by_permaname(
                datasetId
            )

    if dataset_version is None:
        flask.abort(404)

    dataset_version_right = models_controller.get_rights(dataset_version.id)

    dataset = dataset_version.dataset
    dataset_right = models_controller.get_rights(dataset.id)

    dataset.parents = models_controller.filter_allowed_parents(dataset.parents)
    dataset.description = dataset_version.description

    json_dv_data = get_dataset_version_schema_json(
        dataset_version, dataset_version_right
    )

    dataset_schema = schemas.DatasetSchema()
    dataset_schema.context["entry_user_right"] = dataset_right
    subscription = models_controller.get_dataset_subscription_for_dataset_and_user(
        dataset_version.dataset_id
    )
    dataset_schema.context["subscription_id"] = (
        subscription.id if subscription is not None else None
    )
    json_dataset_data = dataset_schema.dump(dataset).data

    # Preparation of the dictonary to return both objects
    json_dv_and_dataset_data = {
        "datasetVersion": json_dv_data,
        "dataset": json_dataset_data,
    }

    return json_dv_and_dataset_data


def _modify_upload_files(
    upload_files: List[UploadS3DataFileDict],
    add_taiga_ids: List[UploadVirtualDataFileDict],
    dataset_version_metadata: Optional[DatasetVersionMetadataDict] = None,
    add_all_existing_files: bool = False,
) -> Tuple[List[UploadS3DataFile], List[UploadVirtualDataFile]]:
    previous_version_taiga_ids: Optional[List[UploadVirtualDataFileDict]] = None

    if dataset_version_metadata is not None:
        dataset_permaname = dataset_version_metadata["dataset"]["permanames"][-1]
        dataset_version = dataset_version_metadata["datasetVersion"]["version"]
        datafiles = dataset_version_metadata["datasetVersion"]["datafiles"]

        # For upload files that have the same content as file in the base dataset version,
        # add the file as a virtual datafile instead of uploading it
        add_as_virtual = {}
        for upload_file_dict in upload_files:
            sha256, md5 = models_controller.get_file_hashes(upload_file_dict["path"])
            matching_file: Optional[DatasetVersionFiles] = next(
                (
                    f
                    for f in datafiles
                    if (
                        f.get("original_file_sha256") == sha256
                        and f.get("original_file_md5") == md5
                        and (
                            models_controller.DATAFILE_UPLOAD_FORMAT_TO_STORAGE_FORMAT[
                                upload_file_dict["format"]
                            ]
                            == f.get("type")
                        )
                    )
                ),
                None,
            )

            if matching_file is not None:
                name: str = upload_file_dict.get(
                    "name",
                    models_controller.standardize_file_name(upload_file_dict["path"]),
                )
                taiga_id = (
                    f"{dataset_permaname}.{dataset_version}/{matching_file['name']}"
                )
                add_as_virtual[upload_file_dict["path"]] = (name, taiga_id)

        add_taiga_ids.extend(
            {"taiga_id": taiga_id, "name": name}
            for _, (name, taiga_id) in add_as_virtual.items()
        )

        upload_files = [
            upload_file_dict
            for upload_file_dict in upload_files
            if upload_file_dict["path"] not in add_as_virtual
        ]

        if add_all_existing_files:
            previous_version_taiga_ids = [
                {
                    "taiga_id": models_controller.format_datafile_id(
                        dataset_permaname, dataset_version, datafile["name"]
                    )
                }
                for datafile in dataset_version_metadata["datasetVersion"]["datafiles"]
            ]

    upload_s3_datafiles = [UploadS3DataFile(f) for f in upload_files]
    upload_virtual_datafiles = [UploadVirtualDataFile(f) for f in add_taiga_ids]
    previous_version_datafiles = (
        [UploadVirtualDataFile(f) for f in previous_version_taiga_ids]
        if previous_version_taiga_ids is not None
        else None
    )

    # https://github.com/python/typeshed/issues/2383
    all_upload_datafiles: Collection[UploadDataFile] = (
        upload_s3_datafiles + upload_virtual_datafiles  # type: ignore
    )

    datafile_names: DefaultDict[str, int] = defaultdict(int)
    for upload_datafile in all_upload_datafiles:
        datafile_names[upload_datafile.file_name] += 1

    duplicate_file_names = [
        file_name for file_name, count in datafile_names.items() if count > 1
    ]
    if len(duplicate_file_names) > 0:
        raise ValueError(
            "Multiple files named {}.".format(", ".join(duplicate_file_names))
        )

    if previous_version_datafiles is not None:
        for upload_datafile in previous_version_datafiles:
            if upload_datafile.file_name not in datafile_names:
                upload_virtual_datafiles.append(upload_datafile)

    return upload_s3_datafiles, upload_virtual_datafiles


def _get_latest_valid_version_from_metadata(
    dataset_metadata: DatasetMetadataDict,
) -> str:
    versions = dataset_metadata["versions"]
    latest_valid_version = 1
    for version in versions:
        version_num = int(version["name"])
        if version_num > latest_valid_version and version["state"] != "deleted":
            latest_valid_version = version_num

    return str(latest_valid_version)


def validate_update_dataset_arguments(
    dataset_metadata: DatasetMetadataDict,
    dataset_permaname: Optional[str],
    dataset_version: Optional[DatasetVersion],
    upload_files: List[UploadS3DataFileDict],
    add_taiga_ids: List[UploadVirtualDataFileDict],
    add_existing_files: bool,
) -> Tuple[
    List[UploadS3DataFile], List[UploadVirtualDataFile], DatasetVersionMetadataDict
]:
    dataset_id = dataset_metadata["datasetId"]
    if dataset_id is not None:
        if "." in dataset_id:
            (
                dataset_permaname,
                dataset_version,
                _,
            ) = models_controller.untangle_dataset_id_with_version(dataset_id)
        else:
            dataset_metadata: DatasetMetadataDict = get_dataset_metadata(
                dataset_id, None
            )
            dataset_permaname = dataset_metadata["permanames"][-1]
    elif dataset_permaname is not None:
        dataset_metadata = get_dataset_metadata(dataset_permaname, None)
    else:
        # TODO standardize exceptions
        raise ValueError("Dataset id or name must be specified.")

    if dataset_version is None:
        dataset_version = _get_latest_valid_version_from_metadata(dataset_metadata)

    dataset_version_metadata: DatasetVersionMetadataDict = (
        get_dataset_metadata(dataset_permaname, dataset_version)
    )

    upload_s3_datafiles, upload_virtual_datafiles = _modify_upload_files(
        upload_files, add_taiga_ids, dataset_version_metadata, add_existing_files
    )

    return upload_s3_datafiles, upload_virtual_datafiles, dataset_version_metadata


def create_new_upload_session():
    upload_session = models_controller.add_new_upload_session()
    return upload_session.id
