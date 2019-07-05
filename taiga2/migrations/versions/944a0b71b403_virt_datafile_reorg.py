"""virt-datafile-reorg

Revision ID: 944a0b71b403
Revises: 92a10cd2cd72
Create Date: 2019-07-05 09:49:25.759335

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '944a0b71b403'
down_revision = '92a10cd2cd72'
branch_labels = None
depends_on = None

datafiletype2 = sa.Enum('s3', 'virtual', name='datafiletype2')
datafileformat = sa.Enum('Raw', 'HDF5', 'Columnar', name='datafileformat')

def upgrade():
    op.execute("insert into datasets (id, permaname) select id, permaname from virtual_datasets")
    op.execute("INSERT INTO dataset_versions (id, dataset_id, version, reason_state, state) SELECT id, virtual_dataset_id, version, reason_state, CAST(CAST( state AS VARCHAR(20) ) AS datasetversionstate) FROM virtual_dataset_versions")
    op.execute("UPDATE entries SET type = 'Dataset' WHERE type = 'VirtualDataset'")
    op.execute("UPDATE entries SET type = 'DatasetVersion' WHERE type = 'VirtualDatasetVersion'")
    datafileformat.create(op.get_bind(), checkfirst=False)
    op.add_column('datafiles', sa.Column('format', datafileformat, nullable=True))
    op.execute("update datafiles set format = CAST ( CAST ( \"type\" as VARCHAR(80) ) as datafileformat) ")
    op.drop_column('datafiles', 'type')
    datafiletype2.create(op.get_bind(), checkfirst=False)
    op.add_column('datafiles', sa.Column('type', datafiletype2, nullable=True))
    op.execute("update datafiles set \"type\" = 's3'")
    op.alter_column('datafiles', 'type', nullable=False)
    op.add_column('datafiles', sa.Column('original_file_sha256', sa.Text(), nullable=True))
    op.add_column('datafiles', sa.Column('underlying_data_file_id', sa.String(length=80), nullable=True))
    op.execute("insert into datafiles (id, name, type, dataset_version_id, underlying_data_file_id) select id, name, 'virtual', virtual_dataset_version_id, data_file_id from virtual_dataset_entries")
    op.create_foreign_key(op.f('fk_datafiles_underlying_data_file_id_datafiles'), 'datafiles', 'datafiles', ['underlying_data_file_id'], ['id'])

    op.add_column('upload_session_files', sa.Column('data_file_id', sa.String(length=80), nullable=True))
    op.add_column('upload_session_files', sa.Column('original_file_sha256', sa.Text(), nullable=True))
    op.create_foreign_key(op.f('fk_upload_session_files_data_file_id_datafiles'), 'upload_session_files', 'datafiles', ['data_file_id'], ['id'])

    # ### end Alembic commands ###



def downgrade():
    raise Exception("unimplemented")
    # ### end Alembic commands ###
