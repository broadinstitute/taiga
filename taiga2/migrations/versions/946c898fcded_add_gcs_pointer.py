"""add-gcs-pointer

Revision ID: 946c898fcded
Revises: d091fc45fa8d
Create Date: 2019-08-13 13:25:26.636789

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "946c898fcded"
down_revision = "d091fc45fa8d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("datafiles", sa.Column("gcs_path", sa.Text(), nullable=True))
    op.add_column("datafiles", sa.Column("generation_id", sa.Text(), nullable=True))
    op.add_column(
        "dataset_versions", sa.Column("changes_description", sa.Text(), nullable=True)
    )
    op.add_column(
        "upload_session_files", sa.Column("gcs_path", sa.Text(), nullable=True)
    )
    op.add_column(
        "upload_session_files", sa.Column("generation_id", sa.Text(), nullable=True)
    )
    # ### end Alembic commands ###
    op.execute("ALTER TABLE datafiles ALTER COLUMN type TYPE VARCHAR(20)")


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("upload_session_files", "generation_id")
    op.drop_column("upload_session_files", "gcs_path")
    op.drop_column("dataset_versions", "changes_description")
    op.drop_column("datafiles", "generation_id")
    op.drop_column("datafiles", "gcs_path")
    # ### end Alembic commands ###