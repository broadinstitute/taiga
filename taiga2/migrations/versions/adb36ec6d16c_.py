"""empty message

Revision ID: adb36ec6d16c
Revises: b2d95ce03b09
Create Date: 2017-05-18 19:30:34.414632

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'adb36ec6d16c'
down_revision = 'b2d95ce03b09'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_logs', sa.Column('entry_id', sa.String(length=80), nullable=True))
    op.drop_constraint('fk_user_logs_dataset_id_datasets', 'user_logs', type_='foreignkey')
    op.create_foreign_key(op.f('fk_user_logs_entry_id_entries'), 'user_logs', 'entries', ['entry_id'], ['id'])
    op.drop_column('user_logs', 'dataset_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_logs', sa.Column('dataset_id', sa.VARCHAR(length=80), autoincrement=False, nullable=True))
    op.drop_constraint(op.f('fk_user_logs_entry_id_entries'), 'user_logs', type_='foreignkey')
    op.create_foreign_key('fk_user_logs_dataset_id_datasets', 'user_logs', 'datasets', ['dataset_id'], ['id'])
    op.drop_column('user_logs', 'entry_id')
    # ### end Alembic commands ###
