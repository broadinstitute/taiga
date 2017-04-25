"""empty message

Revision ID: 530a222a7133
Revises: 9552e419c662
Create Date: 2017-04-25 10:27:07.124984

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '530a222a7133'
down_revision = '9552e419c662'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('provenance_nodes', sa.Column('datafile_id', sa.String(length=80), nullable=True))
    op.drop_constraint('fk_provenance_nodes_dataset_version_id_dataset_versions', 'provenance_nodes', type_='foreignkey')
    op.create_foreign_key(op.f('fk_provenance_nodes_datafile_id_datafiles'), 'provenance_nodes', 'datafiles', ['datafile_id'], ['id'])
    op.drop_column('provenance_nodes', 'dataset_version_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('provenance_nodes', sa.Column('dataset_version_id', sa.VARCHAR(length=80), autoincrement=False, nullable=True))
    op.drop_constraint(op.f('fk_provenance_nodes_datafile_id_datafiles'), 'provenance_nodes', type_='foreignkey')
    op.create_foreign_key('fk_provenance_nodes_dataset_version_id_dataset_versions', 'provenance_nodes', 'dataset_versions', ['dataset_version_id'], ['id'])
    op.drop_column('provenance_nodes', 'datafile_id')
    # ### end Alembic commands ###
