from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.equipment_type import EquipmentTypeRead


class EquipmentBase(BaseModel):
    """Base fields shared by equipment schemas."""

    name: str = Field(min_length=2, max_length=100)
    code: str = Field(min_length=2, max_length=50)
    serial_number: str | None = Field(default=None, max_length=100)
    equipment_type_id: UUID
    location: str = Field(min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=255)
    specifications: dict | None = None
    is_active: bool = True


class EquipmentCreate(EquipmentBase):
    """Payload used to create an equipment unit."""


class EquipmentUpdate(BaseModel):
    """Payload used to update an equipment unit."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    code: str | None = Field(default=None, min_length=2, max_length=50)
    serial_number: str | None = Field(default=None, max_length=100)
    equipment_type_id: UUID | None = None
    location: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=255)
    specifications: dict | None = None
    is_active: bool | None = None


class EquipmentRead(BaseModel):
    """Equipment representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    serial_number: str | None
    location: str
    description: str | None
    specifications: dict | None
    is_active: bool
    equipment_type: EquipmentTypeRead
    created_at: datetime
    updated_at: datetime
