"""create equipment catalog tables

Revision ID: cb6391b9f760
Revises: 25a207d82315
Create Date: 2026-03-18 00:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "cb6391b9f760"
down_revision: Union[str, Sequence[str], None] = "25a207d82315"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "equipment_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_equipment_types_name"), "equipment_types", ["name"], unique=False)

    op.create_table(
        "equipment",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("equipment_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("specifications", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["equipment_type_id"], ["equipment_types.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        sa.UniqueConstraint("serial_number"),
    )
    op.create_index(op.f("ix_equipment_code"), "equipment", ["code"], unique=False)
    op.create_index(op.f("ix_equipment_name"), "equipment", ["name"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(op.f("ix_equipment_name"), table_name="equipment")
    op.drop_index(op.f("ix_equipment_code"), table_name="equipment")
    op.drop_table("equipment")
    op.drop_index(op.f("ix_equipment_types_name"), table_name="equipment_types")
    op.drop_table("equipment_types")
