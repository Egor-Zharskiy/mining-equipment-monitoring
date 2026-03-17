from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.role import RoleRead


class UserBase(BaseModel):
    """Base user fields shared across user schemas."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    is_active: bool = True


class UserCreate(UserBase):
    """Payload used to create a user with assigned roles."""

    password: str = Field(min_length=8, max_length=255)
    role_ids: list[UUID] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """Payload used to update a user and their role assignments."""

    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=255)
    role_ids: list[UUID] | None = None


class UserSelfUpdate(BaseModel):
    """Payload used to update the current user profile."""

    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = None
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)


class UserRead(UserBase):
    """User representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    roles: list[RoleRead]
    created_at: datetime
    updated_at: datetime
