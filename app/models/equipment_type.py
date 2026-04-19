import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EquipmentType(Base):
    """Represents a catalog type of monitored equipment."""

    __tablename__ = "equipment_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    equipment: Mapped[list["Equipment"]] = relationship(back_populates="equipment_type")
    parameter_bindings: Mapped[list["EquipmentTypeParameter"]] = relationship(
        back_populates="equipment_type",
        cascade="all, delete-orphan",
    )
    threshold_rules: Mapped[list["ThresholdRule"]] = relationship(
        back_populates="equipment_type",
        cascade="all, delete-orphan",
    )
    maintenance_plans: Mapped[list["MaintenancePlan"]] = relationship(
        back_populates="equipment_type",
    )
