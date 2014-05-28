"""add missing uk

Revision ID: d0f6f011a68
Revises: 32ebc574f95
Create Date: 2014-05-28 16:50:30.348838

"""

# revision identifiers, used by Alembic.
revision = 'd0f6f011a68'
down_revision = '32ebc574f95'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import *

def upgrade():
  # get rid of dup named_data records
  op.execute("create table named_data_map (orig_named_data_id int, new_named_data_id int)")
  op.execute("insert into named_data_map select n.named_data_id, (select min(i.named_data_id) from named_data i where i.name = n.name ) from named_data n join data_version dv on dv.named_data_id = n.named_data_id")
  op.execute("update data_version set named_data_id = (select new_named_data_id from named_data_map where orig_named_data_id = named_data_id)")
  op.execute("delete from named_data where exists (select 1 from named_data_map where orig_named_data_id = named_data_id and orig_named_data_id <> new_named_data_id)")
  op.drop_table("named_data_map")
  op.create_table('named_data_migrate', 
     Column('named_data_id', Integer, primary_key=True),
     Column('name', String),
     Column('latest_version', Integer),
     UniqueConstraint('name', name='uk_named_data_name')
     )
  op.execute("insert into named_data_migrate (named_data_id, name, latest_version) select named_data_id, name, latest_version from named_data")
  op.drop_table("named_data")
  op.rename_table("named_data_migrate", "named_data")
  
  # fix up versions
  db = op.get_bind()
  r = db.execute("select named_data_id, version, dataset_id from data_version order by named_data_id, created_timestamp").fetchall()
  prev_named_data_id = None
  prev_version = None
  last_version = {}
  for named_data_id, version, dataset_id in r:
    if named_data_id == prev_named_data_id:
      version = prev_version + 1
    prev_named_data_id = named_data_id
    prev_version = version
    last_version[named_data_id] = version
    db.execute("update data_version set version = ? where dataset_id = ?", [version, dataset_id])

  for named_data_id, version in last_version.items():
    db.execute("update named_data set latest_version = ? where named_data_id = ?", [version, named_data_id])

def downgrade():
  op.create_table('named_data_migrate', 
     Column('named_data_id', Integer, primary_key=True),
     Column('name', String),
     Column('latest_version', Integer),
     )
