from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.equipment import EquipmentRead
from app.schemas.equipment_type import EquipmentTypeRead


class MaintenanceUserRead(BaseModel):
    """Compact user representation used in maintenance responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool


class MaintenancePlanCreate(BaseModel):
    """Payload used to create a maintenance plan."""

    equipment_type_id: UUID | None = None
    equipment_id: UUID | None = None
    title: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    interval_hours: int | None = Field(default=None, ge=1)
    interval_days: int | None = Field(default=None, ge=1)
    is_active: bool = True


class MaintenancePlanUpdate(BaseModel):
    """Payload used to update a maintenance plan."""

    equipment_type_id: UUID | None = None
    equipment_id: UUID | None = None
    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    interval_hours: int | None = Field(default=None, ge=1)
    interval_days: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class MaintenancePlanRead(BaseModel):
    """Maintenance plan representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    equipment_type: EquipmentTypeRead | None
    equipment: EquipmentRead | None
    title: str
    description: str | None
    interval_hours: int | None
    interval_days: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MaintenanceTaskCreate(BaseModel):
    """Payload used to create a maintenance task."""

    plan_id: UUID | None = None
    equipment_id: UUID
    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    priority: str = Field(default="medium", min_length=3, max_length=20)
    due_at: datetime | None = None
    assigned_to_user_id: UUID | None = None


class MaintenanceTaskUpdate(BaseModel):
    """Payload used to update a maintenance task."""

    status: str | None = Field(default=None, min_length=3, max_length=20)
    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    priority: str | None = Field(default=None, min_length=3, max_length=20)
    due_at: datetime | None = None
    assigned_to_user_id: UUID | None = None


class MaintenanceTaskRead(BaseModel):
    """Maintenance task representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan: MaintenancePlanRead | None
    equipment: EquipmentRead
    status: str
    priority: str
    title: str
    description: str | None
    due_at: datetime | None
    created_by_user: MaintenanceUserRead | None
    assigned_to_user: MaintenanceUserRead | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class MaintenanceTaskComplete(BaseModel):
    """Payload used to complete a maintenance task and create a record."""

    summary: str = Field(min_length=3, max_length=255)
    details: str | None = Field(default=None, max_length=1000)
    performed_at: datetime
    performed_by_user_id: UUID | None = None


class MaintenanceRecordRead(BaseModel):
    """Maintenance record representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task: MaintenanceTaskRead
    equipment: EquipmentRead
    performed_by_user: MaintenanceUserRead
    summary: str
    details: str | None
    performed_at: datetime
    created_at: datetime
