from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.permission import PermissionRead


class RoleBase(BaseModel):
    """Base role fields shared across role schemas."""

    name: str = Field(min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=255)


class RoleCreate(RoleBase):
    """Payload used to create a role with optional permissions."""

    permission_ids: list[UUID] = Field(default_factory=list)


class RoleRead(RoleBase):
    """Role representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    permissions: list[PermissionRead]
    created_at: datetime
    updated_at: datetime
