"""create maintenance tables

Revision ID: 9a1c6d4e2f7b
Revises: 6f0c3a8d9b1e
Create Date: 2026-04-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "9a1c6d4e2f7b"
down_revision: Union[str, Sequence[str], None] = "6f0c3a8d9b1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "maintenance_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("equipment_type_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("equipment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("interval_hours", sa.Integer(), nullable=True),
        sa.Column("interval_days", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "(equipment_type_id IS NOT NULL AND equipment_id IS NULL) OR "
            "(equipment_type_id IS NULL AND equipment_id IS NOT NULL)",
            name="ck_maintenance_plans_single_target",
        ),
        sa.CheckConstraint(
            "(interval_hours IS NOT NULL AND interval_hours > 0) OR "
            "(interval_days IS NOT NULL AND interval_days > 0)",
            name="ck_maintenance_plans_interval_required",
        ),
        sa.ForeignKeyConstraint(["equipment_type_id"], ["equipment_types.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_maintenance_plans_equipment_type_id", "maintenance_plans", ["equipment_type_id"], unique=False)
    op.create_index("ix_maintenance_plans_equipment_id", "maintenance_plans", ["equipment_id"], unique=False)
    op.create_index("ix_maintenance_plans_is_active", "maintenance_plans", ["is_active"], unique=False)

    op.create_table(
        "maintenance_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("equipment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('open', 'in_progress', 'done', 'cancelled')",
            name="ck_maintenance_tasks_status",
        ),
        sa.CheckConstraint(
            "priority IN ('low', 'medium', 'high')",
            name="ck_maintenance_tasks_priority",
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["maintenance_plans.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_maintenance_tasks_plan_id", "maintenance_tasks", ["plan_id"], unique=False)
    op.create_index("ix_maintenance_tasks_equipment_id", "maintenance_tasks", ["equipment_id"], unique=False)
    op.create_index("ix_maintenance_tasks_status", "maintenance_tasks", ["status"], unique=False)
    op.create_index("ix_maintenance_tasks_priority", "maintenance_tasks", ["priority"], unique=False)
    op.create_index("ix_maintenance_tasks_assigned_to_user_id", "maintenance_tasks", ["assigned_to_user_id"], unique=False)

    op.create_table(
        "maintenance_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("equipment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("performed_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=False),
        sa.Column("details", sa.String(length=1000), nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["maintenance_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["performed_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    op.create_index("ix_maintenance_records_equipment_id", "maintenance_records", ["equipment_id"], unique=False)
    op.create_index("ix_maintenance_records_performed_by_user_id", "maintenance_records", ["performed_by_user_id"], unique=False)
    op.create_index("ix_maintenance_records_performed_at", "maintenance_records", ["performed_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index("ix_maintenance_records_performed_at", table_name="maintenance_records")
    op.drop_index("ix_maintenance_records_performed_by_user_id", table_name="maintenance_records")
    op.drop_index("ix_maintenance_records_equipment_id", table_name="maintenance_records")
    op.drop_table("maintenance_records")

    op.drop_index("ix_maintenance_tasks_assigned_to_user_id", table_name="maintenance_tasks")
    op.drop_index("ix_maintenance_tasks_priority", table_name="maintenance_tasks")
    op.drop_index("ix_maintenance_tasks_status", table_name="maintenance_tasks")
    op.drop_index("ix_maintenance_tasks_equipment_id", table_name="maintenance_tasks")
    op.drop_index("ix_maintenance_tasks_plan_id", table_name="maintenance_tasks")
    op.drop_table("maintenance_tasks")

    op.drop_index("ix_maintenance_plans_is_active", table_name="maintenance_plans")
    op.drop_index("ix_maintenance_plans_equipment_id", table_name="maintenance_plans")
    op.drop_index("ix_maintenance_plans_equipment_type_id", table_name="maintenance_plans")
    op.drop_table("maintenance_plans")
