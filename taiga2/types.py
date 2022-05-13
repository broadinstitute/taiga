import codecs
from enum import Enum
from abc import ABC
import os
from typing import List, Optional
from typing_extensions import Literal, TypedDict

# These types must match the corresponding types in taigapy/types.py
class DataFileType(Enum):
    S3 = "s3"
    Virtual = "virtual"
    GCS = "gcs"


class DataFileUploadFormat(Enum):
    NumericMatrixCSV = "NumericMatrixCSV"
    TableCSV = "TableCSV"
    Raw = "Raw"


User = TypedDict("User", {"id": str, "name": str})
Folder = TypedDict("Folder", {"id": str, "name": str})

DatasetVersionShortDict = TypedDict(
    "DatasetVersionShortDict",
    {"id": str, "name": str, "state": Literal["approved", "deprecated", "deleted"]},
)
DatasetVersionFiles = TypedDict(
    "DatasetVersionFiles",
    {
        "allowed_conversion_type": List[str],  # TODO: remove
        "datafile_type": DataFileType,
        "gcs_path": Optional[str],
        "id": str,
        "name": str,
        "short_summary": str,
        "type": str,  # DataFileFormat
        "underlying_file_id": Optional[str],
        "original_file_md5": Optional[str],
        "original_file_sha256": Optional[str],
    },
)

DataFileMetadataDict = TypedDict(
    "DataFileMetadataDict",
    {
        "dataset_name": str,
        "dataset_permaname": str,
        "dataset_version": str,
        "dataset_id": str,
        "dataset_version_id": str,
        "datafile_name": str,
        "status": str,
        "state": str,
        "reason_state": str,
        "datafile_type": str,
        "datafile_format": str,
        "datafile_encoding": str,
        "urls": Optional[List[str]],
        "underlying_file_id": Optional[str],
    },
)

UploadS3DataFileDict = TypedDict(
    "UploadS3DataFileDict",
    {"path": str, "name": Optional[str], "format": str, "encoding": Optional[str]},
    total=False,
)


class UploadDataFile(ABC):
    file_name: str

    def to_api_param(self):
        pass


class UploadS3DataFile(UploadDataFile):
    def __init__(self, upload_s3_file_dict: UploadS3DataFileDict):
        from taigapy.utils import standardize_file_name

        self.file_path = os.path.abspath(upload_s3_file_dict["path"])
        if not os.path.exists(self.file_path):
            raise Exception(
                "File '{}' does not exist.".format(upload_s3_file_dict["path"])
            )
        self.file_name = upload_s3_file_dict.get(
            "name", standardize_file_name(self.file_path)
        )
        self.datafile_format = DataFileUploadFormat(upload_s3_file_dict["format"])
        self.encoding = codecs.lookup(upload_s3_file_dict.get("encoding", "utf-8")).name
        self.bucket: Optional[str] = None
        self.key: Optional[str] = None

    def add_s3_upload_information(self, bucket: str, key: str):
        self.bucket = bucket
        self.key = key

    def to_api_param(self):
        return {
            "filename": self.file_name,
            "filetype": "s3",
            "s3Upload": {
                "format": self.datafile_format.value,
                "bucket": self.bucket,
                "key": self.key,
                "encoding": self.encoding,
            },
        }


UploadVirtualDataFileDict = TypedDict(
    "UploadVirtualDataFileDict", {"taiga_id": str, "name": str}, total=False
)


class UploadVirtualDataFile(UploadDataFile):
    def __init__(self, upload_virtual_file_dict: UploadVirtualDataFileDict):
        self.taiga_id = upload_virtual_file_dict["taiga_id"]
        self.file_name = upload_virtual_file_dict.get(
            "name", self.taiga_id.split("/", 1)[1]
        )

    def to_api_param(self):
        return {
            "filename": self.file_name,
            "filetype": "virtual",
            "existingTaigaId": self.taiga_id,
        }
