from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic import Field

from app.schemas.equipment import EquipmentRead
from app.schemas.parameter import ParameterRead


class EventRead(BaseModel):
    """Monitoring event representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    equipment: EquipmentRead
    parameter: ParameterRead | None
    telemetry_reading_id: UUID | None
    event_type: str
    severity: str
    title: str
    message: str
    created_at: datetime


class EventMaintenanceTaskCreate(BaseModel):
    """Payload used to create a maintenance task from a monitoring event."""

    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    priority: str = Field(default="high", min_length=3, max_length=20)
    due_at: datetime | None = None
    assigned_to_user_id: UUID | None = None
