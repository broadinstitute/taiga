"""dataset name changes

Revision ID: 26c52ebb3d05
Revises: d0f6f011a68
Create Date: 2014-06-16 10:37:39.308061

"""

# revision identifiers, used by Alembic.
revision = '26c52ebb3d05'
down_revision = 'd0f6f011a68'

from alembic import op
import sqlalchemy as sa
import re

def create_permaname(name, permaname_exists_callback):
  permaname = re.sub("[^A-Za-z0-9]+", "-", name.lower())
  if permaname_exists_callback(permaname):
    suffix = 1
    while True:
      suffixed = "%s-%s" % (permaname, suffix)
      if not permaname_exists_callback(permaname):
        break
      suffix += 1
    permaname = suffixed
  return permaname

def upgrade():
  op.create_table('migrate_named_data', 
       sa.Column('named_data_id', sa.Integer, primary_key=True),
       sa.Column('name', sa.String),
       sa.Column('permaname', sa.String),
       sa.Column('latest_version', sa.Integer),
       sa.Column('is_public', sa.Boolean),
       sa.UniqueConstraint('name', name='uk_named_data_name'),
       sa.UniqueConstraint('permaname', name='uk_perma_named_name')
  )

  db = op.get_bind()

  op.execute("insert into migrate_named_data (named_data_id, name, latest_version) select named_data_id, name, latest_version from named_data")
  for id, name in db.execute("select named_data_id, name from named_data").fetchall():
    db.execute("update migrate_named_data set permaname = ?, is_public = ? where named_data_id = ?", (create_permaname(name, lambda x: False), True, id))
  op.drop_table("named_data")
  op.rename_table("migrate_named_data", "named_data")

  op.create_table('named_data_user',
     sa.Column('id', sa.Integer, primary_key=True),
     sa.Column('named_data_id', sa.Integer, sa.ForeignKey('named_data.named_data_id')),
     sa.Column('user_id', sa.Integer, sa.ForeignKey('user.user_id')),
     sa.UniqueConstraint('named_data_id', "user_id", name='uk_named_data_user'),
  )

def downgrade():
    pass
