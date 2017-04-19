import enum
import uuid
import re
import datetime

from flask_migrate import Migrate

from sqlalchemy import MetaData
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import event

from flask_sqlalchemy import SQLAlchemy

import taiga2.conv as conversion

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

migrate = Migrate()

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)

# Base = declarative_base()

GUID = db.String(80)


def generate_uuid():
    return uuid.uuid4().hex


def generate_str_uuid():
    return str(uuid.uuid4())


# Associations #

# Association table for Many to Many relationship between folder and entries
# As discussed in december 2016 with Philip Montgomery, we decided an entry could have multiple folders containing it
folder_entry_association_table = db.Table('folder_entry_association',
                                          db.Column('folder_id', GUID, db.ForeignKey('folders.id')),
                                          db.Column('entry_id', GUID, db.ForeignKey('entries.id'))
                                          )


# End Associations #


def generate_permaname(name):
    """Generate a permaname based on uuid and the original name"""
    permaname_prefix = name.casefold()  # str.casefold() is a more aggressive .lower()
    permaname_prefix = permaname_prefix.replace('\\', '-')  # Replace '\' by '-'
    # Replace all non alphanumeric by "-"
    permaname_prefix = "".join([c if c.isalnum() else "-" for c in permaname_prefix])
    # TODO: Could also use unicode to remove accents

    # Remove all repetitions of the same non word character (most likely suite of '-')
    permaname_prefix = re.sub(r'(\W)(?=\1)', '', permaname_prefix)

    permaname = permaname_prefix + "-" + str(uuid.uuid4())[:4]

    return permaname


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(GUID, primary_key=True, default=generate_uuid)
    name = db.Column(db.String(80), unique=True)

    email = db.Column(db.TEXT)
    token = db.Column(db.String(50), unique=True, default=generate_str_uuid)

    home_folder_id = db.Column(GUID, db.ForeignKey("folders.id"))
    home_folder = db.relationship("Folder",
                                  foreign_keys="User.home_folder_id",
                                  backref="home_user")

    trash_folder_id = db.Column(GUID, db.ForeignKey("folders.id"))
    trash_folder = db.relationship("Folder",
                                   foreign_keys="User.trash_folder_id",
                                   backref="trash_user")

    def __str__(self):
        return "name: {}, home_folder: {}, trash_folder: {}".format(self.name,
                                                                    self.home_folder.name,
                                                                    self.trash_folder.name)


class UserLog(db.Model):
    __tablename__ = 'user_logs'

    id = db.Column(GUID, primary_key=True, default=generate_uuid)

    user_id = db.Column(GUID, db.ForeignKey("users.id"))
    user = db.relationship("User",
                           foreign_keys="UserLog.user_id",
                           backref="user")

    dataset_id = db.Column(GUID, db.ForeignKey("datasets.id"))
    dataset = db.relationship("Dataset",
                              foreign_keys="UserLog.dataset_id",
                              backref="dataset")
    # TODO: Setup the constraint of only having one (user, dataset) row

    last_access = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Entry(db.Model):
    __tablename__ = 'entries'

    id = db.Column(GUID, primary_key=True, default=generate_uuid)
    name = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))
    creation_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    creator_id = db.Column(GUID, db.ForeignKey("users.id"))

    creator = db.relationship("User",
                              foreign_keys="Entry.creator_id",
                              backref=__tablename__)

    description = db.Column(db.Text)

    __mapper_args__ = {
        'polymorphic_identity': classmethod.__class__.__name__,
        'polymorphic_on': type,
        'with_polymorphic': '*'
    }

    def __str__(self):
        return "Entry name: {}".format(self.name)


class Folder(Entry):
    # Enum Folder types
    # TODO: Could be a good idea to transform these enums into Classes. So they can have different behaviors if needed
    class FolderType(enum.Enum):
        home = 'home'
        trash = 'trash'
        folder = 'folder'

    __tablename__ = 'folders'

    # TODO: Instead of using a string 'entry.id', can we use Entry.id?
    id = db.Column(GUID, db.ForeignKey('entries.id'), primary_key=True)

    folder_type = db.Column(db.Enum(FolderType))

    entries = db.relationship("Entry",
                              secondary=folder_entry_association_table,
                              backref="parents")

    __mapper_args__ = {
        'polymorphic_identity': "Folder"
    }


@event.listens_for(metadata, 'after_create', once=True)
def public_folder_creation(*args, **kwargs):
    """After we create the table Folder, we also add the folder `public`"""
    public_folder = Folder(name="Public",
                           folder_type="folder",
                           description="Public folder accessible by everybody having access to Taiga",
                           id="public")
    db.session.add(public_folder)
    db.session.commit()


class Dataset(Entry):
    __tablename__ = 'datasets'

    id = db.Column(GUID, db.ForeignKey('entries.id'), primary_key=True)

    # TODO: Use the name/key of the dataset and add behind the uuid?
    permaname = db.Column(db.Text)

    __mapper_args__ = {
        'polymorphic_identity': "Dataset"
    }


class InitialFileType(enum.Enum):
    NumericMatrixCSV = "NumericMatrixCSV"
    NumericMatrixTSV = "NumericMatrixTSV"
    Table = "Table"
    GCT = "GCT"
    Raw = "Raw"


class DataFile(db.Model):
    __tablename__ = 'datafiles'

    # IMPORTANT: Need to sync with frontend for each changes
    class DataFileType(enum.Enum):
        Raw = 'Raw'
        HDF5 = 'HDF5'
        Columnar = 'Columnar'

    id = db.Column(GUID, primary_key=True, default=generate_uuid)

    name = db.Column(db.String(80))

    type = db.Column(db.Enum(DataFileType))

    s3_bucket = db.Column(db.Text)
    s3_key = db.Column(db.Text)

    dataset_version_id = db.Column(GUID, db.ForeignKey("dataset_versions.id"))

    dataset_version = db.relationship("DatasetVersion",
                                      foreign_keys=[dataset_version_id],
                                      backref=db.backref(__tablename__,
                                                         cascade="all, delete-orphan"))

    short_summary = db.Column(db.Text)
    long_summary = db.Column(db.Text)


def get_allowed_conversion_type(datafile_type):
    if datafile_type == DataFile.DataFileType.HDF5:
        return [conversion.CSV_FORMAT, conversion.GCT_FORMAT, conversion.HDF5_FORMAT,
                conversion.RDS_FORMAT, conversion.TSV_FORMAT]

    if datafile_type == DataFile.DataFileType.Columnar:
        return [conversion.CSV_FORMAT, conversion.TSV_FORMAT]

    if datafile_type == DataFile.DataFileType.Raw:
        return [conversion.RAW_FORMAT]

    raise Exception("datafile type {} does not exist in the model".format(datafile_type))


_INTIAL_TO_CONVERTED_MAPPING = {InitialFileType.NumericMatrixCSV: DataFile.DataFileType.HDF5,
                                InitialFileType.NumericMatrixTSV: DataFile.DataFileType.HDF5,
                                InitialFileType.GCT: DataFile.DataFileType.HDF5,
                                InitialFileType.Table: DataFile.DataFileType.Columnar,
                                InitialFileType.Raw: DataFile.DataFileType.Raw,
                                }


def find_converted_type_by_initial_type(initial_type):
    return _INTIAL_TO_CONVERTED_MAPPING[initial_type]


class DatasetVersion(Entry):
    # Missing the permaname of the DatasetVersion
    __tablename__ = 'dataset_versions'

    id = db.Column(GUID,
                   db.ForeignKey('entries.id'),
                   primary_key=True)

    dataset_id = db.Column(GUID, db.ForeignKey("datasets.id"))

    dataset = db.relationship("Dataset",
                              foreign_keys=[dataset_id],
                              backref=db.backref(__tablename__),
                              single_parent=True,
                              cascade="all, delete-orphan")

    # Filled out by the server
    version = db.Column(db.Integer)

    # TODO: See how to manage the status (persist.py)

    __mapper_args__ = {
        'polymorphic_identity': "DatasetVersion"
    }


class Activity(db.Model):
    class ActivityType(enum.Enum):
        created = "Created"
        changed_name = "Changed name"
        changed_description = "Changed Description"
        added_version = "Added version"

    __tablename__ = 'activities'

    id = db.Column(GUID, primary_key=True, default=generate_uuid)

    user_id = db.Column(GUID, db.ForeignKey("users.id"))

    user = db.relationship("User",
                           backref=__tablename__)

    dataset_id = db.Column(GUID, db.ForeignKey("datasets.id"))

    dataset = db.relationship("Dataset",
                              backref=__tablename__)

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
    __tablename__ = 'upload_sessions'

    id = db.Column(GUID, primary_key=True, default=generate_uuid)

    user_id = db.Column(GUID, db.ForeignKey('users.id'))
    user = db.relationship("User",
                           backref=__tablename__)


class UploadSessionFile(db.Model):
    __tablename__ = 'upload_session_files'

    id = db.Column(GUID,
                   primary_key=True,
                   default=generate_uuid)

    session_id = db.Column(GUID, db.ForeignKey("upload_sessions.id"))

    session = db.relationship("UploadSession",
                              backref=__tablename__)

    # filename submitted by user
    filename = db.Column(db.Text)

    initial_filetype = db.Column(db.Enum(InitialFileType))
    initial_s3_key = db.Column(db.Text)

    converted_filetype = db.Column(db.Enum(DataFile.DataFileType))
    converted_s3_key = db.Column(db.Text)

    s3_bucket = db.Column(db.Text)

    short_summary = db.Column(db.Text)
    long_summary = db.Column(db.Text)


# <editor-fold desc="Provenance">
class ProvenanceGraph(db.Model):
    __tablename__ = "provenance_graphs"

    graph_id = db.Column(GUID,
                         primary_key=True,
                         default=generate_uuid)

    permaname = db.Column(GUID,
                          unique=True,
                          default=generate_uuid)

    name = db.Column(db.Text)

    created_by_user_id = db.Column(GUID, db.ForeignKey("users.id"))
    user = db.relationship("User",
                           backref=__tablename__)

    created_timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class ProvenanceEdge(db.Model):
    __tablename__ = "provenance_edges"

    edge_id = db.Column(GUID,
                        primary_key=True,
                        default=generate_uuid)

    from_node_id = db.Column(GUID, db.ForeignKey("provenance_nodes.node_id"))
    from_node = db.relationship("ProvenanceNode",
                                foreign_keys="ProvenanceEdge.from_node_id",
                                backref="from_edges")

    to_node_id = db.Column(GUID, db.ForeignKey("provenance_nodes.node_id"))
    to_node = db.relationship("ProvenanceNode",
                              foreign_keys="ProvenanceEdge.to_node_id",
                              backref="to_edges")

    label = db.Column(db.Text)


class ProvenanceNode(db.Model):
    __tablename__ = "provenance_nodes"

    class NodeType(enum.Enum):
        Dataset = "dataset"
        External = "external"
        Process = "process"

    node_id = db.Column(GUID,
                        primary_key=True,
                        default=generate_uuid)

    graph_id = db.Column(GUID, db.ForeignKey("provenance_graphs.graph_id"))
    graph = db.relationship("ProvenanceGraph",
                            backref=__tablename__)

    dataset_version_id = db.Column(GUID, db.ForeignKey("dataset_versions.id"), nullable=True)
    dataset_version = db.relationship("DatasetVersion",
                                      backref=__tablename__)

    label = db.Column(db.Text)

    type = db.Column(db.Enum(NodeType))

# <editor-fold>
