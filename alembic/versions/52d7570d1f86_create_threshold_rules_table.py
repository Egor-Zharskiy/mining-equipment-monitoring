"""create threshold rules table

Revision ID: 52d7570d1f86
Revises: 7d3a8d4e91b2
Create Date: 2026-03-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "52d7570d1f86"
down_revision: Union[str, Sequence[str], None] = "7d3a8d4e91b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "threshold_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("equipment_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parameter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warning_min", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("warning_max", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("critical_min", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("critical_max", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["equipment_type_id"], ["equipment_types.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parameter_id"], ["parameters.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "equipment_type_id",
            "parameter_id",
            name="uq_threshold_rules_equipment_type_id_parameter_id",
        ),
    )
    op.create_index(op.f("ix_threshold_rules_equipment_type_id"), "threshold_rules", ["equipment_type_id"], unique=False)
    op.create_index(op.f("ix_threshold_rules_parameter_id"), "threshold_rules", ["parameter_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(op.f("ix_threshold_rules_parameter_id"), table_name="threshold_rules")
    op.drop_index(op.f("ix_threshold_rules_equipment_type_id"), table_name="threshold_rules")
    op.drop_table("threshold_rules")
