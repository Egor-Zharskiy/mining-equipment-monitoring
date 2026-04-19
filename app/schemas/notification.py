from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.event import EventRead
from app.schemas.maintenance import MaintenanceTaskRead, MaintenanceUserRead


class NotificationCreate(BaseModel):
    """Payload used to create manual notifications."""

    recipient_user_ids: list[UUID] = Field(min_length=1)
    channels: list[str] = Field(default_factory=lambda: ["internal"], min_length=1)
    title: str = Field(min_length=3, max_length=255)
    message: str = Field(min_length=3, max_length=500)


class NotificationRead(BaseModel):
    """Notification representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recipient_user: MaintenanceUserRead
    event: EventRead | None
    maintenance_task: MaintenanceTaskRead | None
    notification_type: str
    channel: str
    title: str
    message: str
    is_read: bool
    read_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime
