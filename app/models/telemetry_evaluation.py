import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TelemetryEvaluation(Base):
    """Stores the evaluation result of a telemetry reading against thresholds."""

    __tablename__ = "telemetry_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telemetry_reading_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("telemetry_readings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
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
    threshold_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("threshold_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    telemetry_reading: Mapped["TelemetryReading"] = relationship(back_populates="evaluation")
    equipment: Mapped["Equipment"] = relationship()
    parameter: Mapped["Parameter"] = relationship()
    threshold_rule: Mapped["ThresholdRule | None"] = relationship(
        back_populates="telemetry_evaluations",
    )
