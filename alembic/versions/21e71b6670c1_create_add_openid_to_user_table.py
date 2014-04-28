"""create add openid to user table

Revision ID: 21e71b6670c1
Revises: 2d0e995ffd9d
Create Date: 2014-04-28 14:47:32.857369

"""

# revision identifiers, used by Alembic.
revision = '21e71b6670c1'
down_revision = '2d0e995ffd9d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table("user_migrate", 
       sa.Column('user_id', sa.Integer, primary_key=True),
       sa.Column('name', sa.String),
       sa.Column('email', sa.String),
       sa.Column('openid', sa.String)
    )
    op.execute("insert into user_migrate (user_id, name, email) select user_id, name, email from user");
    op.drop_table("user")
    op.rename_table("user_migrate", "user")

def downgrade():
    op.create_table("user_migrate", 
       sa.Column('user_id', sa.Integer, primary_key=True),
       sa.Column('name', sa.String),
       sa.Column('email', sa.String)
    )
    op.execute("insert into user_migrate (user_id, name, email) select user_id, name, email from user");
    op.drop_table("user")
    op.rename_table("user_migrate", "user")
