import enum
import uuid
import re
import datetime

from sqlalchemy import MetaData

from flask_sqlalchemy import SQLAlchemy

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)

# Base = declarative_base()

# Associations #

# Association table for Many to Many relationship between folder and entries
# As discussed in december 2016 with Philip Montgomery, we decided an entry could have multiple folders containing it
folder_entry_association_table = db.Table('folder_entry_association',
                                          db.Column('folder_id', db.Integer, db.ForeignKey('folders.id')),
                                          db.Column('entry_id', db.Integer, db.ForeignKey('entries.id'))
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

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    home_folder_id = db.Column(db.Integer, db.ForeignKey("folders.id"))
    home_folder = db.relationship("Folder",
                                  foreign_keys="User.home_folder_id",
                                  backref="home_user")

    trash_folder_id = db.Column(db.Integer, db.ForeignKey("folders.id"))
    trash_folder = db.relationship("Folder",
                                   foreign_keys="User.trash_folder_id",
                                   backref="trash_user")

    def __str__(self):
        return "name: {}, home_folder: {}, trash_folder: {}".format(self.name,
                                                                    self.home_folder.name,
                                                                    self.trash_folder.name)


# TODO: The Entry hierarchy needs to use Single Table Inheritance, based on Philip feedback
class Entry(db.Model):
    __tablename__ = 'entries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(50))
    creation_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    creator = db.relationship("User",
                              foreign_keys="Folder.creator_id",
                              backref=__tablename__)
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
    id = db.Column(db.Integer, db.ForeignKey('entries.id'), primary_key=True)

    folder_type = db.Column(db.Enum(FolderType))
    description = db.Column(db.Text)

    entries = db.relationship("Entry",
                              secondary=folder_entry_association_table,
                              backref="parents")



    __mapper_args__ = {
        'polymorphic_identity': "Folder"
    }


class Dataset(Entry):
    __tablename__ = 'datasets'

    id = db.Column(db.Integer, db.ForeignKey('entries.id'), primary_key=True)

    description = db.Column(db.Text, default="No description provided")

    # TODO: Use the name/key of the dataset and add behind the uuid?
    permaname = db.Column(db.Text)

    __mapper_args__ = {
        'polymorphic_identity': "Dataset"
    }


class DataFile(db.Model):
    # TODO: Can we create a datafile without including it in a datasetVersion?
    __tablename__ = 'datafiles'

    # IMPORTANT: Need to sync with frontend for each changes
    class DataFileType(enum.Enum):
        Raw = 'Raw'
        HDF5 = 'HDF5'
        Columnar = 'Columnar'

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(80))

    type = db.Column(db.Enum(DataFileType))

    url = db.Column(db.Text)

    dataset_version_id = db.Column(db.Integer, db.ForeignKey("dataset_versions.id"))

    dataset_version = db.relationship("DatasetVersion",
                              foreign_keys=[dataset_version_id],
                              backref=db.backref(__tablename__,
                              cascade="all, delete-orphan"))

class DatasetVersion(Entry):
    # Missing the permaname of the DatasetVersion
    __tablename__ = 'dataset_versions'

    id = db.Column(db.Integer,
                   db.ForeignKey('entries.id'),
                   primary_key=True)

    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    creator = db.relationship("User",
                              backref=__tablename__)

    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id"))

    dataset = db.relationship("Dataset",
                              foreign_keys=[dataset_id],
                              backref=db.backref(__tablename__,
                                                 cascade="all, delete-orphan"))

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

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    user = db.relationship("User",
                           backref=__tablename__)

    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id"))

    dataset = db.relationship("Dataset",
                              backref=__tablename__)

    # We would want the type of change and the comments associated
    type = db.Column(db.Enum(ActivityType))

    comments = db.Column(db.Text)

class ConversionCache(db.Model):
    __tablename__ = "conversion_cache"

    id = db.Column(db.Integer, primary_key=True)

    dataset_version_id = db.Column(db.Integer, db.ForeignKey("dataset_versions.id"))

    datafile_name = db.Column(db.String(80))

    format = db.Column(db.String(80))

    status = db.Column(db.Text)

    urls_as_json = db.Column(db.Text)


class UploadSession(db.Model):
    __tablename__ = 'upload_sessions'

    id = db.Column(db.Integer,
                   primary_key=True)


class UploadSessionFile(db.Model):
    __tablename__ = 'upload_session_files'

    id = db.Column(db.Integer,
                   primary_key=True)

    session_id = db.Column(db.Integer, db.ForeignKey("upload_sessions.id"))

    session = db.relationship("UploadSession",
                              backref=__tablename__)

    filename = db.Column(db.Text)

    filetype = db.Column(db.Enum(DataFile.DataFileType))

    url = db.Column(db.Text)
