"""add datafile_previews table

Revision ID: a1b2c3d4e5f6
Revises: c1be0bfabe2e
Create Date: 2026-04-13 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "c1be0bfabe2e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "datafile_previews",
        sa.Column("datafile_id", sa.String(80), sa.ForeignKey("datafiles.id"), primary_key=True),
        sa.Column("preview_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("datafile_previews")
