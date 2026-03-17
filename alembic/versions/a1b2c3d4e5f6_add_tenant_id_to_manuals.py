"""Add tenant_id to underwriting_manuals

Revision ID: a1b2c3d4e5f6
Revises: 8f9a1643b367
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "8f9a1643b367"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "underwriting_manuals",
        sa.Column("tenant_id", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_underwriting_manuals_tenant_id",
        "underwriting_manuals",
        ["tenant_id"],
        unique=False,
    )
    # Back-fill existing rows using the same product-type heuristic so
    # the column is not left NULL for records created before this migration.
    op.execute("""
        UPDATE underwriting_manuals
        SET tenant_id = CASE
            WHEN lower(product_type) LIKE '%life%'              THEN 'admin@heirs-life.com'
            WHEN lower(product_type) LIKE '%gadget%'
              OR lower(product_type) LIKE '%device%'            THEN 'admin@heirs-gadget.com'
            ELSE                                                     'admin@heirs-general.com'
        END
        WHERE tenant_id IS NULL
    """)


def downgrade() -> None:
    op.drop_index("ix_underwriting_manuals_tenant_id", table_name="underwriting_manuals")
    op.drop_column("underwriting_manuals", "tenant_id")
