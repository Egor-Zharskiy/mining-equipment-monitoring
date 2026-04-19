"""create telemetry readings table

Revision ID: 4bb13a4f6f0a
Revises: 8c0c7d8e9f41
Create Date: 2026-03-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "4bb13a4f6f0a"
down_revision: Union[str, Sequence[str], None] = "8c0c7d8e9f41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "telemetry_readings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("equipment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parameter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("value", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parameter_id"], ["parameters.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_telemetry_readings_equipment_id_parameter_id_measured_at",
        "telemetry_readings",
        ["equipment_id", "parameter_id", "measured_at"],
        unique=False,
    )
    op.create_index(
        "ix_telemetry_readings_parameter_id_measured_at",
        "telemetry_readings",
        ["parameter_id", "measured_at"],
        unique=False,
    )
    op.create_index(
        "ix_telemetry_readings_measured_at",
        "telemetry_readings",
        ["measured_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index("ix_telemetry_readings_measured_at", table_name="telemetry_readings")
    op.drop_index("ix_telemetry_readings_parameter_id_measured_at", table_name="telemetry_readings")
    op.drop_index("ix_telemetry_readings_equipment_id_parameter_id_measured_at", table_name="telemetry_readings")
    op.drop_table("telemetry_readings")
