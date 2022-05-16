from abc import ABC
from typing_extensions import TypedDict

# These types must match the corresponding types in taigapy/types.py


class UploadDataFile(ABC):
    file_name: str

    def to_api_param(self):
        pass


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
