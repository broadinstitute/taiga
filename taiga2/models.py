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
# STOP delete


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


# Association table for Many to Many relationship between folder and entries
# As discussed in december 2016 with Philip Montgomery, we decided an entry could have multiple folders containing it
folder_entry_association_table = Table('folder_entry_association',
                                       Base.metadata,
                                       Column('folder_id', Integer, ForeignKey('folders.id')),
                                       Column('entry_id', Integer, ForeignKey('entries.id'))
                                       )


# TODO: The Entry hierarchy needs to use Single Table Inheritance, based on Philip feedback
class Entry(Base):
    __tablename__ = 'entries'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)
    type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
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
                           backref=__tablename__)

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }


class Datafile(Base):
    __tablename__ = 'datafiles'

    id = Column(Integer, primary_key=True)


class Dataset(Entry):
    __tablename__ = 'datasets'

    id = Column(Integer, ForeignKey('entries.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }


class Dataset_version(Entry):
    __tablename__ = 'dataset_versions'

    id = Column(Integer, ForeignKey('entries.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }


class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True)