from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ParameterBase(BaseModel):
    """Base fields shared across parameter schemas."""

    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=100)
    unit: str | None = Field(default=None, max_length=32)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool = True


class ParameterCreate(ParameterBase):
    """Payload used to create a monitoring parameter."""


class ParameterUpdate(BaseModel):
    """Payload used to update a monitoring parameter."""

    code: str | None = Field(default=None, min_length=2, max_length=50)
    name: str | None = Field(default=None, min_length=2, max_length=100)
    unit: str | None = Field(default=None, max_length=32)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class ParameterRead(ParameterBase):
    """Parameter representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
