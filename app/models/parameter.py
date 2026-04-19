import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Parameter(Base):
    """Represents a monitoring metric available in the system."""

    __tablename__ = "parameters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    equipment_type_bindings: Mapped[list["EquipmentTypeParameter"]] = relationship(
        back_populates="parameter",
    )
    threshold_rules: Mapped[list["ThresholdRule"]] = relationship(
        back_populates="parameter",
    )
    telemetry_readings: Mapped[list["TelemetryReading"]] = relationship(
        back_populates="parameter",
    )
    parameter_states: Mapped[list["EquipmentParameterState"]] = relationship(
        back_populates="parameter",
    )
