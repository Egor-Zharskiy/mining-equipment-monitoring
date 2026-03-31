from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.equipment_type import EquipmentTypeRead
from app.schemas.parameter import ParameterRead


class ThresholdRuleBase(BaseModel):
    """Base fields shared across threshold rule schemas."""

    equipment_type_id: UUID
    parameter_id: UUID
    warning_min: Decimal | None = None
    warning_max: Decimal | None = None
    critical_min: Decimal | None = None
    critical_max: Decimal | None = None
    is_active: bool = True


class ThresholdRuleCreate(ThresholdRuleBase):
    """Payload used to create a threshold rule."""


class ThresholdRuleUpdate(BaseModel):
    """Payload used to update a threshold rule."""

    equipment_type_id: UUID | None = None
    parameter_id: UUID | None = None
    warning_min: Decimal | None = None
    warning_max: Decimal | None = None
    critical_min: Decimal | None = None
    critical_max: Decimal | None = None
    is_active: bool | None = None


class ThresholdRuleRead(BaseModel):
    """Threshold rule representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    equipment_type: EquipmentTypeRead
    parameter: ParameterRead
    warning_min: Decimal | None
    warning_max: Decimal | None
    critical_min: Decimal | None
    critical_max: Decimal | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
