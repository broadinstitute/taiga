"""empty message

Revision ID: 028f07e95137
Revises: adb36ec6d16c
Create Date: 2017-07-19 13:50:47.429002

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "028f07e95137"
down_revision = "adb36ec6d16c"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(
        op.f("uq_dataset_versions_dataset_id"),
        "dataset_versions",
        ["dataset_id", "version"],
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        op.f("uq_dataset_versions_dataset_id"), "dataset_versions", type_="unique"
    )
    # ### end Alembic commands ###
