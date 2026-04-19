from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EquipmentTypeBase(BaseModel):
    """Base fields shared by equipment type schemas."""

    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool = True


class EquipmentTypeCreate(EquipmentTypeBase):
    """Payload used to create an equipment type."""


class EquipmentTypeUpdate(BaseModel):
    """Payload used to update an equipment type."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class EquipmentTypeRead(EquipmentTypeBase):
    """Equipment type representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
