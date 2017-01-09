import enum
import uuid
import re

from sqlalchemy import Table, Column, Integer, String, Text, ForeignKey, Enum, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import column_property
from sqlalchemy import select, func


Base = declarative_base()
engine = create_engine('sqlite:///taiga2.db', echo=True)

# TODO: Delete this
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
# STOP delete


# Associations #

# Association for Many to Many relationship between dataset_version and datafile
datasetVersion_dataFile_association_table = Table('datasetVersion_dataFile_association',
                                                  Base.metadata,
                                                  Column('datasetversion_id', Integer, ForeignKey('dataset_versions.id')),
                                                  Column('datafile_id', Integer, ForeignKey('datafiles.id'))
                                                  )


# Association table for Many to Many relationship between folder and entries
# As discussed in december 2016 with Philip Montgomery, we decided an entry could have multiple folders containing it
folder_entry_association_table = Table('folder_entry_association',
                                       Base.metadata,
                                       Column('folder_id', Integer, ForeignKey('folders.id')),
                                       Column('entry_id', Integer, ForeignKey('entries.id'))
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


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    # TODO: Home folder is a specific Folder object
    # home_folder =
    # TODO: Trash folder is a specific Folder object
    # trash_folder =

    def __repr__(self):
        return '<User %r>' % self.name


# TODO: The Entry hierarchy needs to use Single Table Inheritance, based on Philip feedback
class Entry(Versioned, Base):
    __tablename__ = 'entries'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': classmethod.__class__.__name__,
        'polymorphic_on': type,
        'with_polymorphic': '*'
    }


class Folder(Entry):

    # Enum Folder types
    # TODO: Could be a good idea to transform these enums into Classes. So they can have different behaviors if needed
    class FolderType(enum.Enum):
        home = 'home'
        trash = 'trash'
        folder = 'folder'

    __tablename__ = 'folders'

    # TODO: Instead of using a string 'entry.id', can we use Entry.id?
    id = Column(Integer, ForeignKey('entries.id'), primary_key=True)

    folder_type = Column(Enum(FolderType))
    description = Column(Text)

    entries = relationship("Entry",
                           secondary=folder_entry_association_table,
                           backref=__tablename__)

    creator_id = Column(Integer, ForeignKey("users.id"))

    creator = relationship("User",
                           backref="user")

    __mapper_args__ = {
        'polymorphic_identity': "Folder"
    }


class Dataset(Entry):
    __tablename__ = 'datasets'

    id = Column(Integer, ForeignKey('entries.id'), primary_key=True)

    description = Column(Text, default="No description provided")

    # TODO: Use the name/key of the dataset and add behind the uuid?
    permaname = Column(Text, unique=True, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': "Dataset"
    }


class DataFile(Base):
    # TODO: Can we create a datafile without including it in a datasetVersion?
    __tablename__ = 'datafiles'

    id = Column(Integer, primary_key=True)

    name = Column(String(80))

    # To be able to differentiate multiple files with the same name
    permaname = Column(Text, unique=True, nullable=False)

    type = Column(String(80))

    url = Column(Text, unique=True)


class DatasetVersion(Entry):
    __tablename__ = 'dataset_versions'

    id = Column(Integer,
                ForeignKey('entries.id'),
                primary_key=True)

    creator_id = Column(Integer, ForeignKey("users.id"))

    creator = relationship("User",
                           backref=__tablename__)

    dataset_id = Column(Integer, ForeignKey("datasets.id"))

    dataset = relationship("Dataset",
                           foreign_keys=[dataset_id],
                           backref=__tablename__)

    # Filled out by the server
    version = Column(Integer)

    datafiles = relationship("DataFile",
                             secondary=datasetVersion_dataFile_association_table,
                             backref=__tablename__)

    __mapper_args__ = {
        'polymorphic_identity': "DatasetVersion"
    }


class Activity(Base):
    class ActivityType(enum.Enum):
        created = "Created"
        changed_name = "Changed name"
        changed_description = "Changed Description"
        added_version = "Added version"

    __tablename__ = 'activities'

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User",
                        backref=__tablename__)

    dataset_id = Column(Integer, ForeignKey("datasets.id"))

    dataset = relationship("Dataset",
                           backref=__tablename__)

    # We would want the type of change and the comments associated
    type = Column(Enum(ActivityType))

    comments = Column(Text)
