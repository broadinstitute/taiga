"""add is_published and data_type to dataset

Revision ID: 444d181e7dc0
Revises: 21e71b6670c1
Create Date: 2014-04-28 16:12:28.220653

"""

# revision identifiers, used by Alembic.
revision = '444d181e7dc0'
down_revision = '21e71b6670c1'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Boolean


def upgrade():
  op.create_table('data_version_migrate',
       Column('dataset_id', String, primary_key=True),
       Column('named_data_id', Integer, ForeignKey('named_data.named_data_id')),
       Column('version', Integer),
       Column('description', String),
       Column('created_by_user_id', Integer, ForeignKey('user.user_id')),
       Column('created_timestamp', DateTime),
       Column('hdf5_path', String),
       Column('is_published', Boolean),
       Column('data_type', String)
       )
  
  op.execute("insert into data_version_migrate (dataset_id, named_data_id, version, description, created_by_user_id, created_timestamp, hdf5_path) select dataset_id, named_data_id, version, description, created_by_user_id, created_timestamp, hdf5_path from data_version")
  op.drop_table("data_version")
  op.rename_table("data_version_migrate", "data_version")

def downgrade():
  op.create_table('data_version_migrate',
       Column('dataset_id', String, primary_key=True),
       Column('named_data_id', Integer, ForeignKey('named_data.named_data_id')),
       Column('version', Integer),
       Column('description', String),
       Column('created_by_user_id', Integer, ForeignKey('user.user_id')),
       Column('created_timestamp', DateTime),
       Column('hdf5_path', String),
       Column('is_published', Boolean),
       Column('data_type', String)
       )
  op.execute("insert into data_version_migrate (dataset_id, named_data_id, version, description, created_by_user_id, created_timestamp, hdf5_path) select dataset_id, named_data_id, version, description, created_by_user_id, created_timestamp, hdf5_path from data_version")
  op.drop_table("data_version")
  op.rename_table("data_version_migrate", "data_version")
