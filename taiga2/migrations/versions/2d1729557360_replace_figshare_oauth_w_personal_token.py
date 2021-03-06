"""replace figshare oauth w/ personal token

Revision ID: 2d1729557360
Revises: b1e146e20467
Create Date: 2021-01-05 11:39:13.077740

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2d1729557360"
down_revision = "b1e146e20467"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("figshare_authorizations")
    op.add_column(
        "users",
        sa.Column("figshare_personal_token", sa.String(length=128), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("users", "figshare_personal_token")
    op.create_table(
        "figshare_authorizations",
        sa.Column("id", sa.VARCHAR(length=80), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.VARCHAR(length=80), autoincrement=False, nullable=True),
        sa.Column(
            "figshare_account_id", sa.INTEGER(), autoincrement=False, nullable=True
        ),
        sa.Column("token", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("refresh_token", sa.TEXT(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_figshare_authorizations_user_id_users"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_figshare_authorizations"),
    )
    # ### end Alembic commands ###
