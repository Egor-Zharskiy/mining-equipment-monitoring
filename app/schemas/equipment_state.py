from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.equipment import EquipmentRead
from app.schemas.parameter import ParameterRead


class EquipmentParameterStateRead(BaseModel):
    """Current state of a monitored parameter for an equipment unit."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parameter: ParameterRead
    latest_telemetry_reading_id: UUID
    threshold_rule_id: UUID | None
    value: Decimal
    status: str
    measured_at: datetime
    updated_at: datetime


class EquipmentStateRead(BaseModel):
    """Aggregated current monitoring state of an equipment unit."""

    model_config = ConfigDict(from_attributes=True)

    equipment: EquipmentRead
    status: str
    warning_count: int
    critical_count: int
    last_evaluated_at: datetime
    updated_at: datetime


class EquipmentStateDetailRead(EquipmentStateRead):
    """Detailed equipment monitoring state including current parameter snapshots."""

    parameter_states: list[EquipmentParameterStateRead]
