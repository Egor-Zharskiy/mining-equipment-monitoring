"""create monitoring parameter tables

Revision ID: 7d3a8d4e91b2
Revises: cb6391b9f760
Create Date: 2026-03-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "7d3a8d4e91b2"
down_revision: Union[str, Sequence[str], None] = "cb6391b9f760"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "parameters",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_parameters_code"), "parameters", ["code"], unique=False)
    op.create_index(op.f("ix_parameters_name"), "parameters", ["name"], unique=False)

    op.create_table(
        "equipment_type_parameters",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("equipment_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parameter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["equipment_type_id"], ["equipment_types.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parameter_id"], ["parameters.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "equipment_type_id",
            "parameter_id",
            name="uq_equipment_type_parameters_equipment_type_id_parameter_id",
        ),
    )
    op.create_index(
        op.f("ix_equipment_type_parameters_equipment_type_id"),
        "equipment_type_parameters",
        ["equipment_type_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_equipment_type_parameters_parameter_id"),
        "equipment_type_parameters",
        ["parameter_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(op.f("ix_equipment_type_parameters_parameter_id"), table_name="equipment_type_parameters")
    op.drop_index(op.f("ix_equipment_type_parameters_equipment_type_id"), table_name="equipment_type_parameters")
    op.drop_table("equipment_type_parameters")
    op.drop_index(op.f("ix_parameters_name"), table_name="parameters")
    op.drop_index(op.f("ix_parameters_code"), table_name="parameters")
    op.drop_table("parameters")
