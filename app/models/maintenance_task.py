import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MaintenanceTask(Base):
    """Stores a concrete maintenance task for an equipment unit."""

    __tablename__ = "maintenance_tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'in_progress', 'done', 'cancelled')",
            name="ck_maintenance_tasks_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high')",
            name="ck_maintenance_tasks_priority",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("maintenance_plans.id", ondelete="SET NULL"),
        nullable=True,
    )
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    plan: Mapped["MaintenancePlan | None"] = relationship(back_populates="tasks")
    equipment: Mapped["Equipment"] = relationship(back_populates="maintenance_tasks")
    created_by_user: Mapped["User | None"] = relationship(
        foreign_keys=[created_by_user_id],
        back_populates="created_maintenance_tasks",
    )
    assigned_to_user: Mapped["User | None"] = relationship(
        foreign_keys=[assigned_to_user_id],
        back_populates="assigned_maintenance_tasks",
    )
    record: Mapped["MaintenanceRecord | None"] = relationship(
        back_populates="task",
        uselist=False,
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="maintenance_task",
    )
