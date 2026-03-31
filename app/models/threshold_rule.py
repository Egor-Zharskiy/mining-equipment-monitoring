import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ThresholdRule(Base):
    """Stores threshold boundaries for a parameter within an equipment type."""

    __tablename__ = "threshold_rules"
    __table_args__ = (
        UniqueConstraint(
            "equipment_type_id",
            "parameter_id",
            name="uq_threshold_rules_equipment_type_id_parameter_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("equipment_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parameter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parameters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    warning_min: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    warning_max: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    critical_min: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    critical_max: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    equipment_type: Mapped["EquipmentType"] = relationship(back_populates="threshold_rules", lazy="selectin")
    parameter: Mapped["Parameter"] = relationship(back_populates="threshold_rules", lazy="selectin")
