import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MaintenancePlan(Base):
    """Stores a maintenance plan bound to an equipment type or equipment unit."""

    __tablename__ = "maintenance_plans"
    __table_args__ = (
        CheckConstraint(
            "(equipment_type_id IS NOT NULL AND equipment_id IS NULL) OR "
            "(equipment_type_id IS NULL AND equipment_id IS NOT NULL)",
            name="ck_maintenance_plans_single_target",
        ),
        CheckConstraint(
            "(interval_hours IS NOT NULL AND interval_hours > 0) OR "
            "(interval_days IS NOT NULL AND interval_days > 0)",
            name="ck_maintenance_plans_interval_required",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("equipment_types.id", ondelete="CASCADE"),
        nullable=True,
    )
    equipment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    interval_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    equipment_type: Mapped["EquipmentType | None"] = relationship(back_populates="maintenance_plans")
    equipment: Mapped["Equipment | None"] = relationship(back_populates="maintenance_plans")
    tasks: Mapped[list["MaintenanceTask"]] = relationship(
        back_populates="plan",
    )
