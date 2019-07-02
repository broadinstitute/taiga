import enum
import uuid
import re
import datetime
from .extensions import metadata

from flask_migrate import Migrate

from sqlalchemy import event, UniqueConstraint, CheckConstraint

from typing import List

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


def normalize_name(name):
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

    id = db.Column(GUID, primary_key=True, default=generate_uuid)
    name = db.Column(db.String(80), unique=True)

    email = db.Column(db.TEXT)
    token = db.Column(db.String(50), unique=True, default=generate_str_uuid)

    home_folder_id = db.Column(GUID, db.ForeignKey("folders.id"))
    home_folder = db.relationship(
        "Folder", foreign_keys="User.home_folder_id", backref="home_user"
    )

    trash_folder_id = db.Column(GUID, db.ForeignKey("folders.id"))
    trash_folder = db.relationship(
        "Folder", foreign_keys="User.trash_folder_id", backref="trash_user"
    )

    def __str__(self):
        return "name: {}, home_folder: {}, trash_folder: {}".format(
            self.name, self.home_folder.name, self.trash_folder.name
        )


class UserLog(db.Model):
    __tablename__ = "user_logs"

    id = db.Column(GUID, primary_key=True, default=generate_uuid)

    user_id = db.Column(GUID, db.ForeignKey("users.id"))
    user = db.relationship("User", foreign_keys="UserLog.user_id", backref="user")

    entry_id = db.Column(GUID, db.ForeignKey("entries.id"))
    entry = db.relationship("Entry", foreign_keys="UserLog.entry_id", backref="entry")
    # TODO: Setup the constraint of only having one (user, entry) row

    last_access = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Entry(db.Model):
    __tablename__ = "entries"

    id = db.Column(GUID, primary_key=True, default=generate_uuid)
    name = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))
    creation_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    creator_id = db.Column(GUID, db.ForeignKey("users.id"))

    creator = db.relationship(
        "User", foreign_keys="Entry.creator_id", backref=__tablename__
    )

    description = db.Column(db.Text)

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
    id = db.Column(GUID, db.ForeignKey("entries.id"), primary_key=True)

    folder_type = db.Column(db.Enum(FolderType))

    # TODO: This should be a set, not a list.
    entries = db.relationship(
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
    permaname = db.Column(db.Text)

    __mapper_args__ = {"polymorphic_identity": "Dataset"}


class InitialFileType(enum.Enum):
    NumericMatrixCSV = "NumericMatrixCSV"
    NumericMatrixTSV = "NumericMatrixTSV"
    TableCSV = "TableCSV"
    TableTSV = "TableTSV"
    GCT = "GCT"
    Raw = "Raw"


def resolve_virtual_datafile(datafile):
    attempt_count = 0
    while datafile.type == "virtual":
        attempt_count += 1
        if attempt_count > 100:
            raise Exception("Too many virtual references to traverse")
        datafile = datafile.underlying_data_file
    return datafile


class DataFile(db.Model):
    __tablename__ = "datafiles"

    id = db.Column(GUID, primary_key=True, default=generate_uuid)
    name = db.Column(db.String(80))
    type = db.Column(db.String(20))

    dataset_version_id = db.Column(GUID, db.ForeignKey("dataset_versions.id"))
    dataset_version = db.relationship(
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
            "(type = 'virtual' and underlying_data_file_id is not null) or (type = 's3')",
            name="typedcheck",
        ),
    )

    __mapper_args__ = {"polymorphic_on": type, "polymorphic_identity": "abstract"}


class S3DataFile(DataFile):
    # IMPORTANT: Need to sync with frontend for each changes
    class DataFileFormat(enum.Enum):
        Raw = "Raw"
        HDF5 = "HDF5"
        Columnar = "Columnar"

    format = db.Column(db.Enum(DataFileFormat))
    s3_bucket = db.Column(db.Text)
    s3_key = db.Column(db.Text)

    short_summary = db.Column(db.Text)
    long_summary = db.Column(db.Text)
    original_file_sha256 = db.Column(db.Text)

    __mapper_args__ = {"polymorphic_identity": "s3"}

    @property
    def underlying_file_id(self):
        return None


class VirtualDataFile(DataFile):

    __mapper_args__ = {"polymorphic_identity": "virtual"}

    @property
    def underlying_file_id(self):
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
    def s3_bucket(self):
        return None

    @property
    def short_summary(self):
        return self.underlying_data_file.short_summary

    @property
    def long_summary(self):
        return self.underlying_data_file.long_summary

    @property
    def original_file_sha256(self):
        return self.underlying_data_file.original_file_sha256


def get_allowed_conversion_type(datafile_type):
    if datafile_type == S3DataFile.DataFileFormat.HDF5:
        return [
            conversion.CSV_FORMAT,
            conversion.GCT_FORMAT,
            conversion.HDF5_FORMAT,
            conversion.TSV_FORMAT,
        ]

    if datafile_type == S3DataFile.DataFileFormat.Columnar:
        return [conversion.CSV_FORMAT, conversion.TSV_FORMAT]

    if datafile_type == S3DataFile.DataFileFormat.Raw:
        return [conversion.RAW_FORMAT]

    raise Exception(
        "datafile type {} does not exist in the model".format(datafile_type)
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

    id = db.Column(GUID, db.ForeignKey("entries.id"), primary_key=True)

    dataset_id = db.Column(GUID, db.ForeignKey("datasets.id"))

    dataset = db.relationship(
        "Dataset",
        foreign_keys=[dataset_id],
        backref=db.backref(__tablename__),
        single_parent=True,
        cascade="all, delete-orphan",
    )

    # Filled out by the server
    version = db.Column(db.Integer)

    # State of the version
    state = db.Column(
        db.Enum(DatasetVersionState), default=DatasetVersionState.approved
    )
    # Reason for the state of the version. Should be empty if approved
    reason_state = db.Column(db.Text)

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

    __tablename__ = "activities"

    id = db.Column(GUID, primary_key=True, default=generate_uuid)

    user_id = db.Column(GUID, db.ForeignKey("users.id"))

    user = db.relationship("User", backref=__tablename__)

    dataset_id = db.Column(GUID, db.ForeignKey("datasets.id"))

    dataset = db.relationship("Dataset", backref=__tablename__)

    # We would want the type of change and the comments associated
    type = db.Column(db.Enum(ActivityType))

    comments = db.Column(db.Text)


class ConversionEntryState(enum.Enum):
    failed = "Failed"
    running = "Running"
    complete = "Complete"


class ConversionCache(db.Model):
    __tablename__ = "conversion_cache"

    id = db.Column(GUID, primary_key=True, default=generate_uuid)

    dataset_version_id = db.Column(GUID, db.ForeignKey("dataset_versions.id"))

    datafile_name = db.Column(db.String(80))

    format = db.Column(db.String(80))

    status = db.Column(db.Text)

    task_id = db.Column(db.Text)

    urls_as_json = db.Column(db.Text)

    state = db.Column(db.Enum(ConversionEntryState))


class UploadSession(db.Model):
    __tablename__ = "upload_sessions"

    id = db.Column(GUID, primary_key=True, default=generate_uuid)

    user_id = db.Column(GUID, db.ForeignKey("users.id"))
    user = db.relationship("User", backref=__tablename__)


class UploadSessionFile(db.Model):
    __tablename__ = "upload_session_files"

    id = db.Column(GUID, primary_key=True, default=generate_uuid)

    session_id = db.Column(GUID, db.ForeignKey("upload_sessions.id"))

    session = db.relationship("UploadSession", backref=__tablename__)

    # filename submitted by user
    filename = db.Column(db.Text)

    initial_filetype = db.Column(db.Enum(InitialFileType))
    initial_s3_key = db.Column(db.Text)

    converted_filetype = db.Column(db.Enum(S3DataFile.DataFileFormat))
    converted_s3_key = db.Column(db.Text)

    s3_bucket = db.Column(db.Text)

    short_summary = db.Column(db.Text)
    long_summary = db.Column(db.Text)
    original_file_sha256 = db.Column(db.Text)

    data_file_id = db.Column(GUID, db.ForeignKey("datafiles.id"))
    data_file = db.relationship(
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

    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)

    name = db.Column(db.String(80))

    users = db.relationship(
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


# </editor-fold>
