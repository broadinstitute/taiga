"""update old create timestamps

Revision ID: 3845a4513dbb
Revises: 444d181e7dc0
Create Date: 2014-04-29 16:05:34.912991

"""

# revision identifiers, used by Alembic.
revision = '3845a4513dbb'
down_revision = '444d181e7dc0'

from alembic import op
import sqlalchemy as sa
import datetime


def upgrade():
  db = op.get_bind()
  r = db.execute("select dataset_id, created_timestamp from data_version").fetchall()
  for dataset_id, timestamp in r:
    try:
      ts = float(timestamp)
    except ValueError:
      continue
    new_timestamp=datetime.datetime.utcfromtimestamp(ts)
    db.execute("update data_version set created_timestamp = ? where dataset_id = ?", [new_timestamp, dataset_id])

def downgrade():
    pass
