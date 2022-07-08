import enum
from sqlite3 import Timestamp
import uuid
import re
import datetime
from xmlrpc.client import DateTime
from .extensions import metadata

from flask_migrate import Migrate

from sqlalchemy import event, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import backref
from sqlalchemy.ext.declarative import declared_attr

from typing import Dict, List

import taiga2.conv as conversion
from taiga2.extensions import db

migrate = Migrate()

# Base = declarative_base()

GUID = db.String(80)


def generate_uuid():
    return uuid.uuid4().hex


def generate_str_uuid():
    return str(uuid.uuid4())


# Associations #

# Association table for Many to Many relationship between folder and entries
# As discussed in december 2016 with Philip Montgomery, we decided an entry could have multiple folders containing it
folder_entry_association_table = db.Table(
    "folder_entry_association",
    db.Column("folder_id", GUID, db.ForeignKey("folders.id")),
    db.Column("entry_id", GUID, db.ForeignKey("entries.id")),
)

group_user_association_table = db.Table(
    "group_user_association",
    db.Column("group_id", db.INTEGER, db.ForeignKey("groups.id")),
    db.Column("user_id", GUID, db.ForeignKey("users.id")),
)


# End Associations #


def normalize_name(name: str) -> str:
    permaname_prefix = name.casefold()  # str.casefold() is a more aggressive .lower()
    permaname_prefix = permaname_prefix.replace("\\", "-")  # Replace '\' by '-'
    # Replace all non alphanumeric by "-"
    permaname_prefix = "".join([c if c.isalnum() else "-" for c in permaname_prefix])
    # TODO: Could also use unicode to remove accents

    # Remove all repetitions of the same non word character (most likely suite of '-')
    permaname_prefix = re.sub(r"(\W)(?=\1)", "", permaname_prefix)
    return permaname_prefix


def generate_permaname(name):
    """Generate a permaname based on uuid and the original name"""
    permaname = normalize_name(name) + "-" + str(uuid.uuid4())[:4]

    return permaname


class User(db.Model):
    __tablename__ = "users"

    id: str = db.Column(GUID, primary_key=True, default=generate_uuid)
    name: str = db.Column(db.String(80), unique=True)

    email: str = db.Column(db.TEXT)
    token: str = db.Column(db.String(50), unique=True, default=generate_str_uuid)

    home_folder_id: str = db.Column(GUID, db.ForeignKey("folders.id"))
    home_folder: "Folder" = db.relationship(
        "Folder", foreign_keys="User.home_folder_id", backref="home_user"
    )

    trash_folder_id: str = db.Column(GUID, db.ForeignKey("folders.id"))
    trash_folder: "Folder" = db.relationship(
        "Folder", foreign_keys="User.trash_folder_id", backref="trash_user"
    )

    figshare_personal_token: str = db.Column(db.String(128), nullable=True)

    def __str__(self):
        return "name: {}, home_folder: {}, trash_folder: {}".format(
            self.name, self.home_folder.name, self.trash_folder.name
        )


class UserLog(db.Model):
    __tablename__ = "user_logs"

    id: str = db.Column(GUID, primary_key=True, default=generate_uuid)

    user_id: str = db.Column(GUID, db.ForeignKey("users.id"))
    user: User = db.relationship("User", foreign_keys="UserLog.user_id", backref="user")

    entry_id: str = db.Column(GUID, db.ForeignKey("entries.id"))
    entry: "Entry" = db.relationship(
        "Entry", foreign_keys="UserLog.entry_id", backref="entry"
    )
    # TODO: Setup the constraint of only having one (user, entry) row

    last_access: datetime.datetime = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )


class Entry(db.Model):
    __tablename__ = "entries"

    id: str = db.Column(GUID, primary_key=True, default=generate_uuid)
    name: str = db.Column(db.Text, nullable=False)
    type: str = db.Column(db.String(50))
    creation_date: datetime.datetime = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )

    creator_id: str = db.Column(GUID, db.ForeignKey("users.id"))

    creator: User = db.relationship(
        "User", foreign_keys="Entry.creator_id", backref=__tablename__
    )

    description: str = db.Column(db.Text)

    __mapper_args__ = {
        "polymorphic_identity": classmethod.__class__.__name__,
        "polymorphic_on": type,
        "with_polymorphic": "*",
    }

    def __str__(self):
        return "Entry name: {}".format(self.name)


class Folder(Entry):
    # Enum Folder types
    # TODO: Could be a good idea to transform these enums into Classes. So they can have different behaviors if needed
    class FolderType(enum.Enum):
        home = "home"
        trash = "trash"
        folder = "folder"

    __tablename__ = "folders"

    # TODO: Instead of using a string 'entry.id', can we use Entry.id?
    id: str = db.Column(GUID, db.ForeignKey("entries.id"), primary_key=True)

    folder_type: FolderType = db.Column(db.Enum(FolderType))

    # TODO: This should be a set, not a list.
    entries: List[Entry] = db.relationship(
        "Entry", secondary=folder_entry_association_table, backref="parents"
    )

    __mapper_args__ = {"polymorphic_identity": "Folder"}

    def __repr__(self):
        return "Folder name: {} and id: {}".format(self.name, self.id)


@event.listens_for(metadata, "after_create")
def public_folder_creation(*args, **kwargs):
    """After we create the table Folder, we also add the folder `public`"""
    public_folder = Folder(
        name="Public",
        folder_type="folder",
        description="Public folder accessible by everybody having access to Taiga",
        id="public",
    )
    db.session.add(public_folder)
    db.session.commit()


class Dataset(Entry):
    __tablename__ = "datasets"

    id = db.Column(GUID, db.ForeignKey("entries.id"), primary_key=True)

    # TODO: Use the name/key of the dataset and add behind the uuid?
    permanames: List["DatasetPermaname"] = db.relationship("DatasetPermaname")

    @property
    def permaname(self) -> str:
        if len(self.permanames) > 0:
            return max(
                self.permanames, key=lambda permaname: permaname.creation_date
            ).permaname
        return ""

    __mapper_args__ = {"polymorphic_identity": "Dataset"}


class DatasetPermaname(db.Model):
    __tablename__ = "dataset_permanames"

    permaname: str = db.Column(db.Text, primary_key=True)
    dataset_id: str = db.Column(GUID, db.ForeignKey("datasets.id"))
    creation_date: datetime.datetime = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )


class InitialFileType(enum.Enum):
    NumericMatrixCSV = "NumericMatrixCSV"
    NumericMatrixTSV = "NumericMatrixTSV"
    TableCSV = "TableCSV"
    TableTSV = "TableTSV"
    GCT = "GCT"
    Raw = "Raw"


def resolve_virtual_datafile(datafile) -> "S3DataFile":
    attempt_count = 0
    while datafile.type == "virtual":
        attempt_count += 1
        if attempt_count > 100:
            raise Exception("Too many virtual references to traverse")
        datafile = datafile.underlying_data_file
    return datafile


class DataFile(db.Model):
    __tablename__ = "datafiles"

    id: str = db.Column(GUID, primary_key=True, default=generate_uuid)
    name: str = db.Column(db.String(80))
    type: str = db.Column(db.String(20))

    dataset_version_id: str = db.Column(GUID, db.ForeignKey("dataset_versions.id"))
    dataset_version: "DatasetVersion" = db.relationship(
        "DatasetVersion",
        foreign_keys=[dataset_version_id],
        backref=db.backref(__tablename__, cascade="all, delete-orphan"),
    )

    # these two columns really belong to VirtualDataFile, but SQLAlchemy seems to have some problems with
    # self-referencing FKs. Moved here to get it to work, but assume these will be both None unless the type is
    # VirtualDataFile. Also underlying_data_file_id is always None. Use underlying_data_file.id instead if you want the ID
    underlying_data_file_id = db.Column(GUID, db.ForeignKey("datafiles.id"))
    underlying_data_file = db.relationship("DataFile", remote_side=[id])

    __table_args__ = (
        UniqueConstraint("dataset_version_id", "name"),
        CheckConstraint(
            "(type = 'virtual' and underlying_data_file_id is not null) or (type = 's3') or (type = 'gcs')",
            name="typedcheck",
        ),
    )

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "abstract"}


class ReadAccessLog(db.Model):
    __tablename__ = "read_access_log"

    datafile_id: int = db.Column(db.String, primary_key=True)
    user_id: str = db.Column(db.String, primary_key=True)
    first_access: datetime.datetime = db.Column(db.DateTime)
    last_access: datetime.datetime = db.Column(db.DateTime)
    access_count: int = db.Column(db.Integer, default=1)

    def __repr__(self):
        return "Datafile id: {}, User id: {}, First access: {}, Last access: {}, Access count: {}".format(
            self.datafile_id,
            self.user_id,
            self.first_access,
            self.last_access,
            self.access_count,
        )


class S3DataFile(DataFile):
    # IMPORTANT: Need to sync with frontend for each changes
    class DataFileFormat(enum.Enum):
        Raw = "Raw"
        HDF5 = "HDF5"
        Columnar = "Columnar"

    format: DataFileFormat = db.Column(db.Enum(DataFileFormat))
    encoding = db.Column(db.Text)
    s3_bucket: str = db.Column(db.Text)
    s3_key: str = db.Column(db.Text)
    compressed_s3_key: str = db.Column(db.Text)

    short_summary: str = db.Column(db.Text)
    long_summary: str = db.Column(db.Text)
    column_types_as_json: Dict[str, str] = db.Column(db.JSON)
    original_file_sha256: str = db.Column(db.Text)
    original_file_md5: str = db.Column(db.Text)

    __mapper_args__ = {"polymorphic_identity": "s3"}

    @property
    def underlying_file_id(self):
        return None


class VirtualDataFile(DataFile):

    __mapper_args__ = {"polymorphic_identity": "virtual"}

    @property
    def underlying_file_id(self):
        # assert self.underlying_data_file.type != "virtual"
        dataset_version = self.underlying_data_file.dataset_version
        return "{}.{}/{}".format(
            dataset_version.dataset.permaname,
            dataset_version.version,
            self.underlying_data_file.name,
        )

    @property
    def s3_key(self):
        return None

    @property
    def compressed_s3_key(self):
        return None

    @property
    def s3_bucket(self):
        return None

    @property
    def short_summary(self):
        return self.underlying_data_file.short_summary

    @property
    def format(self):
        # assert self.underlying_data_file.type != "virtual"
        return self.underlying_data_file.format

    @property
    def long_summary(self):
        return self.underlying_data_file.long_summary

    @property
    def original_file_sha256(self):
        return self.underlying_data_file.original_file_sha256

    @property
    def original_file_md5(self):
        return self.underlying_data_file.original_file_md5


class GCSObjectDataFile(DataFile):
    __mapper_args__ = {"polymorphic_identity": "gcs"}

    gcs_path: str = db.Column(db.Text)
    generation_id: str = db.Column(db.Text)

    @property
    def underlying_file_id(self):
        return None


def get_allowed_conversion_type(datafile: S3DataFile) -> List[str]:
    if datafile.format == S3DataFile.DataFileFormat.HDF5:
        allowed_conversion_types = [
            conversion.CSV_FORMAT,
            conversion.GCT_FORMAT,
            conversion.HDF5_FORMAT,
            conversion.TSV_FORMAT,
        ]

        if datafile.compressed_s3_key is not None:
            allowed_conversion_types.insert(0, conversion.COMPRESSED_FORMAT)

        return allowed_conversion_types

    if datafile.format == S3DataFile.DataFileFormat.Columnar:
        allowed_conversion_types = [conversion.CSV_FORMAT, conversion.TSV_FORMAT]

        if datafile.compressed_s3_key is not None:
            allowed_conversion_types.insert(0, conversion.COMPRESSED_FORMAT)

        return allowed_conversion_types

    if datafile.format == S3DataFile.DataFileFormat.Raw:
        return [conversion.RAW_FORMAT]

    raise Exception(
        "datafile type {} does not exist in the model".format(datafile.type)
    )


_INTIAL_TO_CONVERTED_MAPPING = {
    InitialFileType.NumericMatrixCSV: S3DataFile.DataFileFormat.HDF5,
    InitialFileType.NumericMatrixTSV: S3DataFile.DataFileFormat.HDF5,
    InitialFileType.GCT: S3DataFile.DataFileFormat.HDF5,
    InitialFileType.TableCSV: S3DataFile.DataFileFormat.Columnar,
    InitialFileType.TableTSV: S3DataFile.DataFileFormat.Columnar,
    InitialFileType.Raw: S3DataFile.DataFileFormat.Raw,
}


def find_converted_type_by_initial_type(initial_type):
    return _INTIAL_TO_CONVERTED_MAPPING[initial_type]


class DatasetVersion(Entry):
    class DatasetVersionState(enum.Enum):
        approved = "Approved"
        deprecated = "Deprecated"
        deleted = "Deleted"

    # TODO: Missing the permaname of the DatasetVersion
    __tablename__ = "dataset_versions"

    id: str = db.Column(GUID, db.ForeignKey("entries.id"), primary_key=True)

    dataset_id: str = db.Column(GUID, db.ForeignKey("datasets.id"))

    dataset: Dataset = db.relationship(
        "Dataset",
        foreign_keys=[dataset_id],
        backref=db.backref(__tablename__),
        single_parent=True,
        cascade="all, delete-orphan",
    )

    # Filled out by the server
    version: int = db.Column(db.Integer)

    # State of the version
    state: DatasetVersionState = db.Column(
        db.Enum(DatasetVersionState), default=DatasetVersionState.approved
    )
    # Reason for the state of the version. Should be empty if approved
    reason_state: str = db.Column(db.Text)

    changes_description: str = db.Column(db.Text)

    __table_args__ = (UniqueConstraint("dataset_id", "version"),)

    # TODO: See how to manage the status (persist.py)

    __mapper_args__ = {"polymorphic_identity": "DatasetVersion"}


#########


class Activity(db.Model):
    class ActivityType(enum.Enum):
        created = "Created"
        changed_name = "Changed name"
        changed_description = "Changed Description"
        added_version = "Added version"
        started_log = "Log started"

    __tablename__ = "activities"

    id: str = db.Column(GUID, primary_key=True, default=generate_uuid)

    user_id: str = db.Column(GUID, db.ForeignKey("users.id"))

    user: User = db.relationship("User", backref=__tablename__)

    dataset_id: str = db.Column(GUID, db.ForeignKey("datasets.id"))

    dataset: Dataset = db.relationship("Dataset", backref=__tablename__)

    # We would want the type of change and the comments associated
    type: ActivityType = db.Column(db.Enum(ActivityType), nullable=False)

    timestamp: datetime.datetime = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )

    comments: str = db.Column(db.Text)

    __mapper_args__ = {"polymorphic_on": type}


class CreationActivity(Activity):
    __mapper_args__ = {"polymorphic_identity": Activity.ActivityType.created}

    @declared_attr
    def dataset_name(cls) -> str:
        return Activity.__table__.c.get("dataset_name", db.Column(db.Text))

    @declared_attr
    def dataset_description(cls) -> str:
        return Activity.__table__.c.get("dataset_description", db.Column(db.Text))


class NameUpdateActivity(Activity):
    __mapper_args__ = {"polymorphic_identity": Activity.ActivityType.changed_name}

    @declared_attr
    def dataset_name(cls) -> str:
        return Activity.__table__.c.get("dataset_name", db.Column(db.Text))


class DescriptionUpdateActivity(Activity):
    __mapper_args__ = {
        "polymorphic_identity": Activity.ActivityType.changed_description
    }

    @declared_attr
    def dataset_description(cls) -> str:
        return Activity.__table__.c.get("dataset_description", db.Column(db.Text))

    @declared_attr
    def dataset_version(cls) -> int:
        return Activity.__table__.c.get("dataset_version", db.Column(db.Integer))


class VersionAdditionActivity(Activity):
    __mapper_args__ = {"polymorphic_identity": Activity.ActivityType.added_version}

    @declared_attr
    def dataset_description(cls) -> str:
        return Activity.__table__.c.get("dataset_description", db.Column(db.Text))

    @declared_attr
    def dataset_version(cls) -> str:
        return Activity.__table__.c.get("dataset_version", db.Column(db.Integer))


class LogStartActivity(Activity):
    __mapper_args__ = {"polymorphic_identity": Activity.ActivityType.started_log}

    @declared_attr
    def dataset_name(cls) -> str:
        return Activity.__table__.c.get("dataset_name", db.Column(db.Text))

    @declared_attr
    def dataset_description(cls) -> str:
        return Activity.__table__.c.get("dataset_description", db.Column(db.Text))

    @declared_attr
    def dataset_version(cls) -> str:
        return Activity.__table__.c.get("dataset_version", db.Column(db.Integer))


class LockTable(db.Model):
    __tablename__ = "lock_table"

    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    random: int = db.Column(db.Integer)


class ConversionEntryState(enum.Enum):
    failed = "Failed"
    running = "Running"
    complete = "Complete"


class ConversionCache(db.Model):
    __tablename__ = "conversion_cache"

    id: str = db.Column(GUID, primary_key=True, default=generate_uuid)

    dataset_version_id: str = db.Column(GUID, db.ForeignKey("dataset_versions.id"))

    datafile_name: str = db.Column(db.String(80))

    format: str = db.Column(db.String(80))

    status: str = db.Column(db.Text)

    task_id: str = db.Column(db.Text)

    urls_as_json: str = db.Column(db.Text)

    state: ConversionEntryState = db.Column(db.Enum(ConversionEntryState))


class UploadSession(db.Model):
    __tablename__ = "upload_sessions"

    id: str = db.Column(GUID, primary_key=True, default=generate_uuid)

    user_id: str = db.Column(GUID, db.ForeignKey("users.id"))
    user: User = db.relationship("User", backref=__tablename__)


class UploadSessionFile(db.Model):
    __tablename__ = "upload_session_files"

    id: str = db.Column(GUID, primary_key=True, default=generate_uuid)

    session_id: str = db.Column(GUID, db.ForeignKey("upload_sessions.id"))

    session: UploadSession = db.relationship("UploadSession", backref=__tablename__)

    # filename submitted by user
    filename: str = db.Column(db.Text)
    encoding: str = db.Column(db.Text)

    initial_filetype: InitialFileType = db.Column(db.Enum(InitialFileType))
    initial_s3_key: str = db.Column(db.Text)

    converted_filetype: S3DataFile.DataFileFormat = db.Column(
        db.Enum(S3DataFile.DataFileFormat)
    )
    converted_s3_key: str = db.Column(db.Text)

    compressed_s3_key: str = db.Column(db.Text)

    s3_bucket: str = db.Column(db.Text)

    gcs_path: str = db.Column(db.Text)
    generation_id: str = db.Column(db.Text)

    short_summary: str = db.Column(db.Text)
    long_summary: str = db.Column(db.Text)
    column_types_as_json: Dict[str, str] = db.Column(db.JSON)
    original_file_sha256: str = db.Column(db.Text)
    original_file_md5: str = db.Column(db.Text)

    data_file_id: str = db.Column(GUID, db.ForeignKey("datafiles.id"))
    data_file: DataFile = db.relationship(
        "DataFile", uselist=False, foreign_keys="UploadSessionFile.data_file_id"
    )


# <editor-fold desc="Provenance">
class ProvenanceGraph(db.Model):
    __tablename__ = "provenance_graphs"

    graph_id = db.Column(GUID, primary_key=True, default=generate_uuid)

    permaname = db.Column(GUID, unique=True, default=generate_uuid)

    name = db.Column(db.Text)

    created_by_user_id = db.Column(GUID, db.ForeignKey("users.id"), nullable=True)
    user = db.relationship("User", backref=__tablename__)

    created_timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class ProvenanceEdge(db.Model):
    __tablename__ = "provenance_edges"

    edge_id = db.Column(GUID, primary_key=True, default=generate_uuid)

    from_node_id = db.Column(GUID, db.ForeignKey("provenance_nodes.node_id"))
    from_node = db.relationship(
        "ProvenanceNode",
        foreign_keys="ProvenanceEdge.from_node_id",
        backref="from_edges",
    )

    to_node_id = db.Column(GUID, db.ForeignKey("provenance_nodes.node_id"))
    to_node = db.relationship(
        "ProvenanceNode", foreign_keys="ProvenanceEdge.to_node_id", backref="to_edges"
    )

    label = db.Column(db.Text)


class ProvenanceNode(db.Model):
    __tablename__ = "provenance_nodes"

    class NodeType(enum.Enum):
        Dataset = "dataset"
        External = "external"
        Process = "process"

    node_id = db.Column(GUID, primary_key=True, default=generate_uuid)

    graph_id = db.Column(GUID, db.ForeignKey("provenance_graphs.graph_id"))
    graph = db.relationship("ProvenanceGraph", backref=__tablename__)

    datafile_id = db.Column(GUID, db.ForeignKey("datafiles.id"), nullable=True)
    datafile = db.relationship("DataFile", backref=__tablename__)

    label = db.Column(db.Text)

    type = db.Column(db.Enum(NodeType))


# </editor-fold>

# <editor-fold desc="ACLs">


class Group(db.Model):
    __tablename__ = "groups"

    id: str = db.Column(db.INTEGER, primary_key=True, autoincrement=True)

    name: str = db.Column(db.String(80))

    users: List[User] = db.relationship(
        User.__name__, secondary=group_user_association_table, backref=__tablename__
    )

    def __repr__(self):
        return "Group {}".format(self.name)


@event.listens_for(metadata, "after_create")
def admin_group_creation(*args, **kwargs):
    """After we create the table Group, we also add the group 'Admin'"""
    admin_group = Group(name="Admin")

    db.session.add(admin_group)
    db.session.commit()


class EntryRightsEnum(enum.Enum):
    can_edit = "can_edit"
    can_view = "can_view"


# </editor-fold>

# <editor-fold desc="Search">
class Breadcrumb:
    """Object tracking the path we took to find a specific entry when performing a search
    Should contain the entry (folder) we pass through, and its order
    """

    def __init__(self, order: int, folder: Folder):
        self.order = order
        self.folder = folder


class SearchEntry:
    """Object resulting from a search.
    Should contain the entry found and breadcrumbs (path to reach the entry)
    """

    def __init__(self, entry: Entry, breadcrumbs: List[Breadcrumb]):
        self.entry = entry
        self.breadcrumbs = breadcrumbs


class SearchResult:
    """Container object of a search.
    Should contain the root folder we search from, the name of the search and the entries fetched from the search
    """

    def __init__(self, current_folder: Folder, name: str, entries: List[SearchEntry]):
        self.current_folder = current_folder
        self.name = name
        self.entries = entries


class ThirdPartyDatasetVersionLink(db.Model):
    __tablename__ = "third_party_dataset_version_links"

    id: str = db.Column(GUID, primary_key=True, default=generate_uuid)
    type: str = db.Column(db.String(50))

    creator_id: str = db.Column(GUID, db.ForeignKey("users.id"))
    creator: User = db.relationship(
        "User",
        foreign_keys="ThirdPartyDatasetVersionLink.creator_id",
        backref=__tablename__,
    )

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "abstract"}


class FigshareDatasetVersionLink(ThirdPartyDatasetVersionLink):
    __tablename__ = "figshare_dataset_version_links"

    id: str = db.Column(
        GUID, db.ForeignKey("third_party_dataset_version_links.id"), primary_key=True
    )
    figshare_article_id: int = db.Column(db.Integer, nullable=False)
    figshare_article_version: int = db.Column(db.Integer, nullable=False)
    dataset_version_id: str = db.Column(GUID, db.ForeignKey("dataset_versions.id"))
    dataset_version: DatasetVersion = db.relationship(
        "DatasetVersion",
        backref=backref("figshare_dataset_version_link", uselist=False),
    )
    figshare_datafile_links: List["FigshareDataFileLink"] = db.relationship(
        "FigshareDataFileLink"
    )
    __mapper_args__ = {"polymorphic_identity": "figshare"}


class ThirdPartyDataFileLink(db.Model):
    __tablename__ = "third_party_datafile_links"

    id: str = db.Column(GUID, primary_key=True, default=generate_uuid)
    type: str = db.Column(db.String(50))
    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "abstract"}


class FigshareDataFileLink(ThirdPartyDataFileLink):
    __tablename__ = "figshare_datafile_links"

    id: str = db.Column(
        GUID, db.ForeignKey("third_party_datafile_links.id"), primary_key=True
    )
    figshare_file_id: int = db.Column(db.Integer, nullable=False)
    datafile_id: str = db.Column(GUID, db.ForeignKey("datafiles.id"))
    datafile: DataFile = db.relationship(
        "DataFile", backref=backref("figshare_datafile_link", uselist=False)
    )
    figshare_dataset_version_link_id: str = db.Column(
        GUID, db.ForeignKey("figshare_dataset_version_links.id")
    )

    __mapper_args__ = {"polymorphic_identity": "figshare"}


class DatasetSubscription(db.Model):
    __tablename__ = "dataset_subscriptions"

    id: str = db.Column(GUID, primary_key=True, default=generate_uuid)
    user: User = db.relationship("User", backref=__tablename__)
    user_id: str = db.Column(GUID, db.ForeignKey("users.id"))

    dataset: Dataset = db.relationship("Dataset", backref=__tablename__)
    dataset_id: str = db.Column(GUID, db.ForeignKey("datasets.id"))
