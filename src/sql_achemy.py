from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey

engine = create_engine('sqlite:///:memory:', echo=True)
metadata = MetaData()

named_data = Table('named_data', metadata,
     Column('named_data_id', Integer, primary_key=True),
     Column('name', String),
     Column('latest_version', Integer),
)

data_version = Table('data_version', metadata,
     Column('dataset_id', Integer, primary_key=True),
     Column('named_data_id', None, ForeignKey('named_data.named_data_id')),
     Column('version', Integer),
     Column('description', String),
     Column('created_by_user_id', None, ForeignKey('user.user_id')),
     Column('created_timestamp', Datetime),
     Column('hdf5_path', String)
)

user = Table('user', metadata, 
     Column('user_id', Integer, primary_key=True),
     Column('name', String),
     Column('email', String),
)