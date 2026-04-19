"""create events table

Revision ID: 6f0c3a8d9b1e
Revises: 5b2f5c0d3e8b
Create Date: 2026-03-31 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "6f0c3a8d9b1e"
down_revision: Union[str, Sequence[str], None] = "5b2f5c0d3e8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SEVERITY_CHECK = "severity IN ('normal', 'warning', 'critical')"


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("equipment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parameter_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("telemetry_reading_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(SEVERITY_CHECK, name="ck_events_severity"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parameter_id"], ["parameters.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["telemetry_reading_id"], ["telemetry_readings.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_equipment_id", "events", ["equipment_id"], unique=False)
    op.create_index("ix_events_parameter_id", "events", ["parameter_id"], unique=False)
    op.create_index("ix_events_severity", "events", ["severity"], unique=False)
    op.create_index("ix_events_event_type", "events", ["event_type"], unique=False)
    op.create_index("ix_events_created_at", "events", ["created_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index("ix_events_created_at", table_name="events")
    op.drop_index("ix_events_event_type", table_name="events")
    op.drop_index("ix_events_severity", table_name="events")
    op.drop_index("ix_events_parameter_id", table_name="events")
    op.drop_index("ix_events_equipment_id", table_name="events")
    op.drop_table("events")
