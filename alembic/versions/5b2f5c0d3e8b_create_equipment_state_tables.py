"""create equipment state tables

Revision ID: 5b2f5c0d3e8b
Revises: 4bb13a4f6f0a
Create Date: 2026-03-31 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "5b2f5c0d3e8b"
down_revision: Union[str, Sequence[str], None] = "4bb13a4f6f0a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUS_CHECK = "status IN ('normal', 'warning', 'critical')"


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "telemetry_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("telemetry_reading_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("equipment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parameter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("threshold_rule_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(STATUS_CHECK, name="ck_telemetry_evaluations_status"),
        sa.ForeignKeyConstraint(["telemetry_reading_id"], ["telemetry_readings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parameter_id"], ["parameters.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["threshold_rule_id"], ["threshold_rules.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telemetry_reading_id"),
    )
    op.create_index("ix_telemetry_evaluations_equipment_id", "telemetry_evaluations", ["equipment_id"], unique=False)
    op.create_index("ix_telemetry_evaluations_parameter_id", "telemetry_evaluations", ["parameter_id"], unique=False)
    op.create_index("ix_telemetry_evaluations_status", "telemetry_evaluations", ["status"], unique=False)

    op.create_table(
        "equipment_parameter_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("equipment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parameter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("latest_telemetry_reading_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("threshold_rule_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("value", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(STATUS_CHECK, name="ck_equipment_parameter_states_status"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parameter_id"], ["parameters.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["latest_telemetry_reading_id"], ["telemetry_readings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["threshold_rule_id"], ["threshold_rules.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "equipment_id",
            "parameter_id",
            name="uq_equipment_parameter_states_equipment_id_parameter_id",
        ),
    )
    op.create_index(
        "ix_equipment_parameter_states_equipment_id",
        "equipment_parameter_states",
        ["equipment_id"],
        unique=False,
    )
    op.create_index(
        "ix_equipment_parameter_states_status",
        "equipment_parameter_states",
        ["status"],
        unique=False,
    )

    op.create_table(
        "equipment_states",
        sa.Column("equipment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("warning_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("critical_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(STATUS_CHECK, name="ck_equipment_states_status"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("equipment_id"),
    )
    op.create_index("ix_equipment_states_status", "equipment_states", ["status"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index("ix_equipment_states_status", table_name="equipment_states")
    op.drop_table("equipment_states")
    op.drop_index("ix_equipment_parameter_states_status", table_name="equipment_parameter_states")
    op.drop_index("ix_equipment_parameter_states_equipment_id", table_name="equipment_parameter_states")
    op.drop_table("equipment_parameter_states")
    op.drop_index("ix_telemetry_evaluations_status", table_name="telemetry_evaluations")
    op.drop_index("ix_telemetry_evaluations_parameter_id", table_name="telemetry_evaluations")
    op.drop_index("ix_telemetry_evaluations_equipment_id", table_name="telemetry_evaluations")
    op.drop_table("telemetry_evaluations")
