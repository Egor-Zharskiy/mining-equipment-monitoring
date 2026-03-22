from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.equipment_type import EquipmentTypeRead
from app.schemas.parameter import ParameterRead


class EquipmentTypeParameterCreate(BaseModel):
    """Payload used to bind a parameter to an equipment type."""

    equipment_type_id: UUID
    parameter_id: UUID
    is_required: bool = True


class EquipmentTypeParameterRead(BaseModel):
    """Equipment type parameter binding returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    equipment_type: EquipmentTypeRead
    parameter: ParameterRead
    is_required: bool
    created_at: datetime
    updated_at: datetime
