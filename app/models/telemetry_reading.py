import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TelemetryReading(Base):
    """Stores a raw telemetry measurement for a piece of equipment."""

    __tablename__ = "telemetry_readings"

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
    value: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    equipment: Mapped["Equipment"] = relationship(back_populates="telemetry_readings")
    parameter: Mapped["Parameter"] = relationship(back_populates="telemetry_readings")
    evaluation: Mapped["TelemetryEvaluation | None"] = relationship(
        back_populates="telemetry_reading",
        uselist=False,
        cascade="all, delete-orphan",
    )
