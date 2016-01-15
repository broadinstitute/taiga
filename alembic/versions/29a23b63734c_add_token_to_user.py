"""add token to user

Revision ID: 29a23b63734c
Revises: 358789c7fdd0
Create Date: 2016-01-15 15:42:25.937069

"""

# revision identifiers, used by Alembic.
revision = '29a23b63734c'
down_revision = '358789c7fdd0'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table("user_migrate",
       sa.Column('user_id', sa.Integer, primary_key=True),
       sa.Column('name', sa.String),
       sa.Column('email', sa.String),
       sa.Column('openid', sa.String),
       sa.Column('token', sa.String)
    )
    op.execute("insert into user_migrate (user_id, name, email, openid) select user_id, name, email, openid from user");
    op.drop_table("user")
    op.rename_table("user_migrate", "user")

def downgrade():
    pass
