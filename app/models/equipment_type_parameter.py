import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EquipmentTypeParameter(Base):
    """Links equipment types to supported monitoring parameters."""

    __tablename__ = "equipment_type_parameters"
    __table_args__ = (
        UniqueConstraint(
            "equipment_type_id",
            "parameter_id",
            name="uq_equipment_type_parameters_equipment_type_id_parameter_id",
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
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    equipment_type: Mapped["EquipmentType"] = relationship(back_populates="parameter_bindings", lazy="selectin")
    parameter: Mapped["Parameter"] = relationship(back_populates="equipment_type_bindings", lazy="selectin")
