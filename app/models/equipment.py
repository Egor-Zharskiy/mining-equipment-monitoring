import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Equipment(Base):
    """Represents a concrete unit of equipment under monitoring."""

    __tablename__ = "equipment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    equipment_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("equipment_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    location: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    specifications: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    equipment_type: Mapped["EquipmentType"] = relationship(back_populates="equipment")
    telemetry_readings: Mapped[list["TelemetryReading"]] = relationship(
        back_populates="equipment",
    )
    parameter_states: Mapped[list["EquipmentParameterState"]] = relationship(
        back_populates="equipment",
        cascade="all, delete-orphan",
    )
    current_state: Mapped["EquipmentState | None"] = relationship(
        back_populates="equipment",
        cascade="all, delete-orphan",
        uselist=False,
    )
    maintenance_plans: Mapped[list["MaintenancePlan"]] = relationship(
        back_populates="equipment",
    )
    maintenance_tasks: Mapped[list["MaintenanceTask"]] = relationship(
        back_populates="equipment",
    )
    maintenance_records: Mapped[list["MaintenanceRecord"]] = relationship(
        back_populates="equipment",
    )
