"""add prov graphs

Revision ID: 8e7e1f77044
Revises: 476dc32d164b
Create Date: 2016-05-23 12:46:00.081816

"""

# revision identifiers, used by Alembic.
revision = '8e7e1f77044'
down_revision = '476dc32d164b'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime

def upgrade():
    op.create_table("prov_graph",
                  Column("graph_id", Integer, primary_key=True),
                  Column("permaname", String),
                  Column("name", String),
                  Column('created_by_user_id', Integer, ForeignKey('user.user_id')),
                  Column('created_timestamp', DateTime),
                  sqlite_autoincrement=True)
    op.create_table("prov_node",
                      Column("node_id", Integer, primary_key=True),
                      Column("graph_id", Integer, ForeignKey('prov_graph.graph_id')),
                      Column("dataset_id", String, ForeignKey('data_version.dataset_id')),
                      Column("label", String),
                      Column("type", String),
                      sqlite_autoincrement=True)
    op.create_table("prov_edge",
                  Column("edge_id", Integer, primary_key=True),
                  Column("graph_id", Integer, ForeignKey('prov_graph.graph_id')),
                  Column("from_node_id", Integer, ForeignKey('prov_node.node_id')),
                  Column("to_node_id", Integer, ForeignKey('prov_node.node_id')),
                  Column("label", String),
                  sqlite_autoincrement=True)


def downgrade():
    pass



