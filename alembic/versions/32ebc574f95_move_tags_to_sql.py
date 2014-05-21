"""move tags to sql

Revision ID: 32ebc574f95
Revises: e90607d972e
Create Date: 2014-05-21 16:50:43.241256

"""

# revision identifiers, used by Alembic.
revision = '32ebc574f95'
down_revision = 'e90607d972e'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Boolean


def upgrade():
  op.create_table('named_data_tag',
       Column('named_data_tag_id', Integer, primary_key=True),
       Column('named_data_id', Integer, ForeignKey('named_data.named_data_id')),
       Column('tag', String), sqlite_autoincrement=True
       )
  op.execute("insert into named_data_tag (named_data_id, tag) select dv.named_data_id, s.object from statement s join data_version dv on dv.dataset_id = s.subject where s.predicate = 'hasTag'")

def downgrade():
  op.drop_table("named_data_tag")
