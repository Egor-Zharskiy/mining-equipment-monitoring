from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PermissionBase(BaseModel):
    """Base permission fields shared across permission schemas."""

    code: str = Field(min_length=3, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class PermissionCreate(PermissionBase):
    """Payload used to create a permission."""


class PermissionRead(PermissionBase):
    """Permission representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
