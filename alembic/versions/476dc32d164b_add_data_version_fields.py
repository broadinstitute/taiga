"""add data version fields

Revision ID: 476dc32d164b
Revises: 29a23b63734c
Create Date: 2016-03-01 15:27:07.751310

"""

# revision identifiers, used by Alembic.
revision = '476dc32d164b'
down_revision = '29a23b63734c'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table("data_version_migrate",
        sa.Column('dataset_id', sa.String, primary_key=True),
        sa.Column('named_data_id', sa.Integer, sa.ForeignKey('named_data.named_data_id')),
        sa.Column('version', sa.Integer),
        sa.Column('description', sa.String),
        sa.Column('created_by_user_id', sa.Integer, sa.ForeignKey('user.user_id')),
        sa.Column('created_timestamp', sa.DateTime),
        sa.Column('hdf5_path', sa.String),
        sa.Column('columnar_path', sa.String),
        sa.Column('is_published', sa.Boolean),
        sa.Column('data_type', sa.String),
        sa.Column('is_deprecated', sa.Boolean),
        sa.Column('uploaded_md5', sa.String),
        sa.Column('downloaded_count', sa.Integer))

    columns = "dataset_id, named_data_id,version,description,created_by_user_id,created_timestamp,hdf5_path,columnar_path,is_published,data_type"
    op.execute("insert into data_version_migrate ("+columns+") select "+columns+" from data_version")
    op.drop_table("data_version")
    op.rename_table("data_version_migrate", "data_version")


