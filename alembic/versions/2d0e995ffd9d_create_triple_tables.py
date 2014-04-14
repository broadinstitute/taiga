"""create triple tables

Revision ID: 2d0e995ffd9d
Revises: None
Create Date: 2014-04-14 13:00:51.947478

"""

# revision identifiers, used by Alembic.
revision = '2d0e995ffd9d'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table("statements", 
        sa.Column("statement_id", sa.Integer, primary_key=True),
        sa.Column('subject', sa.String, nullable=False),
        sa.Column('predicate', sa.String, nullable=False),
        sa.Column('object_type', sa.Integer, nullable=False),
        sa.Column('object', sa.String, nullable=False)
        )        

def downgrade():
    op.drop_table("statements")
