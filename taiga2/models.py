import enum

from sqlalchemy import Table, Column, Integer, String, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()
engine = create_engine('sqlite:///taiga2.db', echo=True)

# TODO: Delete this
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()
# STOP delere


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    # TODO: Home folder is a specific Folder object
    # home_folder =
    # TODO: Trash folder is a specific Folder object
    # trash_folder =

    def __repr__(self):
        return '<User %r>' % self.name


# Association table for Many to Many relationship between folder and entries
# As discussed in december 2016 with Philip Montgomery, we decided an entry could have multiple folders containing it
folder_entry_association_table = Table('folder_entry_association',
                                       Base.metadata,
                                       Column('folder_id', Integer, ForeignKey('folder.id')),
                                       Column('entry_id', Integer, ForeignKey('entry.id'))
                                       )


# TODO: The Entry hierarchy needs to use Single Table Inheritance, based on Philip feedback
class Entry(Base):
    __tablename__ = 'entry'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'entry',
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

    __tablename__ = 'folder'

    # TODO: Instead of using a string 'entry.id', can we use Entry.id?
    id = Column(Integer, ForeignKey('entry.id'), primary_key=True)

    folder_type = Column(Enum(FolderType))
    description = Column(Text)

    entries = relationship("Entry",
                           secondary=folder_entry_association_table,
                           backref="folders")

    __mapper_args__ = {
        'polymorphic_identity': 'folder',
    }


class Datafile(Base):
    __tablename__ = 'datafile'

    id = Column(Integer, primary_key=True)


class Dataset(Entry):
    __tablename__ = 'dataset'

    id = Column(Integer, ForeignKey('entry.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'dataset',
    }


class Dataset_version(Entry):
    __tablename__ = 'dataset_version'

    id = Column(Integer, ForeignKey('entry.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'dataset_version',
    }


class Activity(Base):
    __tablename__ = 'activity'
    id = Column(Integer, primary_key=True)