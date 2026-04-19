from datetime import datetime, timedelta
from uuid import UUID

from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.equipment_type_parameter_repository import \
    EquipmentTypeParameterRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.telemetry_reading_repository import \
    TelemetryReadingRepository
from app.services.equipment_state_service import EquipmentStateService
from app.schemas.telemetry_reading import TelemetryReadingCreate


class TelemetryReadingService:
    """Encapsulates business rules for telemetry ingestion."""

    def __init__(
            self,
            telemetry_reading_repository: TelemetryReadingRepository,
            equipment_repository: EquipmentRepository,
            parameter_repository: ParameterRepository,
            equipment_type_parameter_repository: EquipmentTypeParameterRepository,
            equipment_state_service: EquipmentStateService,
    ) -> None:
        """Store repository dependencies used by the service."""

        self._telemetry_reading_repository = telemetry_reading_repository
        self._equipment_repository = equipment_repository
        self._parameter_repository = parameter_repository
        self._equipment_type_parameter_repository = equipment_type_parameter_repository
        self._equipment_state_service = equipment_state_service

    async def create_reading(self, payload: TelemetryReadingCreate):
        """Create a new raw telemetry reading after domain validation."""


        equipment = await self._equipment_repository.get_by_id(
            payload.equipment_id)
        if equipment is None:
            raise ValueError("Equipment was not found.")

        parameter = await self._parameter_repository.get_by_id(
            payload.parameter_id)
        if parameter is None:
            raise ValueError("Parameter was not found.")

        binding = await self._equipment_type_parameter_repository.get_by_equipment_type_and_parameter(
            equipment_type_id=equipment.equipment_type_id,
            parameter_id=parameter.id,
        )
        if binding is None:
            raise ValueError(
                "Parameter is not assigned to the equipment type of the target equipment.")

        self._validate_measured_at(payload.measured_at)

        telemetry_reading = await self._telemetry_reading_repository.create(
            equipment=equipment,
            parameter=parameter,
            value=payload.value,
            measured_at=payload.measured_at,
        )

        await self._equipment_state_service.process_new_reading(
            telemetry_reading)
        return await self._telemetry_reading_repository.get_by_id(
            telemetry_reading.id)

    async def list_readings(
            self,
            *,
            equipment_id: UUID | None = None,
            parameter_id: UUID | None = None,
            date_from: datetime | None = None,
            date_to: datetime | None = None,
            limit: int = 100,
    ):
        """Return telemetry readings with optional filters."""

        if date_from is not None and date_to is not None and date_from > date_to:
            raise ValueError(
                "date_from must be less than or equal to date_to.")

        return await self._telemetry_reading_repository.list_all(
            equipment_id=equipment_id,
            parameter_id=parameter_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

    async def get_reading(self, reading_id: UUID):
        """Return a telemetry reading by identifier."""

        return await self._telemetry_reading_repository.get_by_id(reading_id)

    @staticmethod
    def _validate_measured_at(measured_at: datetime) -> None:
        """Reject timestamps that are unreasonably far in the future."""

        if measured_at.tzinfo is None:
            raise ValueError("measured_at must include timezone information.")

        if measured_at > datetime.now(measured_at.tzinfo) + timedelta(
                minutes=5):
            raise ValueError(
                "measured_at cannot be more than 5 minutes in the future.")
