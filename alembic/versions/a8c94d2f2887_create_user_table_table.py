"""create user table table

Revision ID: a8c94d2f2887
Revises:
Create Date: 2025-05-22 17:02:26.821655

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a8c94d2f2887"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("username", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
    )

    op.create_table(
        "api_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("token", sa.String(), unique=True, index=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
    )


def downgrade():
    op.drop_table("api_tokens")
    op.drop_table("users")
