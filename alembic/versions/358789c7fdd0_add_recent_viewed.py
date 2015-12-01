"""add recent_viewed

Revision ID: 358789c7fdd0
Revises: 3cf245f2fcab
Create Date: 2015-10-08 15:05:55.341877

"""

# revision identifiers, used by Alembic.
revision = '358789c7fdd0'
down_revision = '3cf245f2fcab'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('view_history', 
    sa.Column('view_history_id', sa.Integer, primary_key=True),
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.user_id')),
    sa.Column('dataset_id', sa.String),
    sa.Column('latest_view', sa.DateTime),
    sa.Column('view_count', sa.Integer),
    sa.UniqueConstraint('user_id', 'dataset_id', name='uk_view_history'),
    sqlite_autoincrement=True
    )



def downgrade():
    op.drop_table('view_history')
