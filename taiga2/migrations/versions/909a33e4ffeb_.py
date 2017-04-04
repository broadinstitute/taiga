"""empty message

Revision ID: 909a33e4ffeb
Revises: 
Create Date: 2017-03-06 20:56:54.313706

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '909a33e4ffeb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('fk_dataset_versions_creator_id_users', 'dataset_versions', type_='foreignkey')
    op.drop_column('dataset_versions', 'creator_id')
    op.drop_column('datasets', 'description')
    op.add_column('entries', sa.Column('description', sa.Text(), nullable=True))
    op.drop_column('folders', 'description')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('folders', sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True))
    op.drop_column('entries', 'description')
    op.add_column('datasets', sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('dataset_versions', sa.Column('creator_id', sa.VARCHAR(length=80), autoincrement=False, nullable=True))
    op.create_foreign_key('fk_dataset_versions_creator_id_users', 'dataset_versions', 'users', ['creator_id'], ['id'])
    # ### end Alembic commands ###