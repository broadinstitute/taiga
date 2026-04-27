"""add datafile_previews table

Revision ID: 495216f833f4
Revises: c1be0bfabe2e
Create Date: 2026-04-27 12:44:54.336754

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "495216f833f4"
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
