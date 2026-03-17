"""Add session_id and user_email to chat_logs

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chat_logs", sa.Column("session_id", sa.String(), nullable=True))
    op.add_column("chat_logs", sa.Column("user_email", sa.String(), nullable=True))
    op.create_index("ix_chat_logs_session_id", "chat_logs", ["session_id"], unique=False)
    op.create_index("ix_chat_logs_user_email", "chat_logs", ["user_email"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_chat_logs_user_email", table_name="chat_logs")
    op.drop_index("ix_chat_logs_session_id", table_name="chat_logs")
    op.drop_column("chat_logs", "user_email")
    op.drop_column("chat_logs", "session_id")
