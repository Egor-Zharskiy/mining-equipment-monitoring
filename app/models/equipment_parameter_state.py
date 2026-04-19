import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EquipmentParameterState(Base):
    """Stores the latest evaluated state of a parameter for an equipment unit."""

    __tablename__ = "equipment_parameter_states"
    __table_args__ = (
        UniqueConstraint(
            "equipment_id",
            "parameter_id",
            name="uq_equipment_parameter_states_equipment_id_parameter_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("equipment.id", ondelete="CASCADE"),
        nullable=False,
    )
    parameter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parameters.id", ondelete="RESTRICT"),
        nullable=False,
    )
    latest_telemetry_reading_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("telemetry_readings.id", ondelete="CASCADE"),
        nullable=False,
    )
    threshold_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threshold_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    value: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    equipment: Mapped["Equipment"] = relationship(back_populates="parameter_states")
    parameter: Mapped["Parameter"] = relationship(back_populates="parameter_states")
    latest_telemetry_reading: Mapped["TelemetryReading"] = relationship()
    threshold_rule: Mapped["ThresholdRule | None"] = relationship()
