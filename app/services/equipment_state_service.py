from decimal import Decimal
from uuid import UUID

from app.core.monitoring import (
    METRIC_STATUS_CRITICAL,
    METRIC_STATUS_NORMAL,
    METRIC_STATUS_WARNING,
    VALID_MONITORING_STATUSES,
)
from app.repositories.equipment_parameter_state_repository import EquipmentParameterStateRepository
from app.repositories.equipment_state_repository import EquipmentStateRepository
from app.repositories.telemetry_evaluation_repository import TelemetryEvaluationRepository
from app.repositories.threshold_rule_repository import ThresholdRuleRepository
from app.services.event_service import EventService


class EquipmentStateService:
    """Encapsulates telemetry evaluation and current equipment state aggregation."""

    def __init__(
        self,
        threshold_rule_repository: ThresholdRuleRepository,
        telemetry_evaluation_repository: TelemetryEvaluationRepository,
        equipment_parameter_state_repository: EquipmentParameterStateRepository,
        equipment_state_repository: EquipmentStateRepository,
        event_service: EventService,
    ) -> None:
        """Store repository dependencies used by the service."""

        self._threshold_rule_repository = threshold_rule_repository
        self._telemetry_evaluation_repository = telemetry_evaluation_repository
        self._equipment_parameter_state_repository = equipment_parameter_state_repository
        self._equipment_state_repository = equipment_state_repository
        self._event_service = event_service

    async def process_new_reading(self, telemetry_reading):
        """Evaluate a new reading and update current state snapshots."""

        equipment = telemetry_reading.equipment
        parameter = telemetry_reading.parameter
        previous_equipment_state = await self._equipment_state_repository.get_by_equipment_id(equipment.id)
        previous_equipment_status = previous_equipment_state.status if previous_equipment_state is not None else None

        rule = await self._threshold_rule_repository.get_by_equipment_type_and_parameter(
            equipment_type_id=equipment.equipment_type_id,
            parameter_id=parameter.id,
        )

        if rule is None or not rule.is_active:
            raise ValueError("Active threshold rule was not found for the equipment parameter pair.")

        status = self._calculate_metric_status(
            value=telemetry_reading.value,
            warning_min=rule.warning_min,
            warning_max=rule.warning_max,
            critical_min=rule.critical_min,
            critical_max=rule.critical_max,
        )

        await self._telemetry_evaluation_repository.create(
            telemetry_reading=telemetry_reading,
            equipment=equipment,
            parameter=parameter,
            threshold_rule=rule,
            status=status,
        )

        parameter_state = await self._equipment_parameter_state_repository.get_by_equipment_and_parameter(
            equipment_id=equipment.id,
            parameter_id=parameter.id,
        )
        previous_parameter_status = parameter_state.status if parameter_state is not None else None
        if parameter_state is None:
            await self._equipment_parameter_state_repository.create(
                equipment=equipment,
                parameter=parameter,
                latest_telemetry_reading=telemetry_reading,
                threshold_rule=rule,
                value=telemetry_reading.value,
                status=status,
                measured_at=telemetry_reading.measured_at,
            )
        else:
            await self._equipment_parameter_state_repository.update(
                parameter_state,
                latest_telemetry_reading=telemetry_reading,
                threshold_rule=rule,
                value=telemetry_reading.value,
                status=status,
                measured_at=telemetry_reading.measured_at,
            )
        parameter_states = await self._equipment_parameter_state_repository.list_by_equipment(equipment.id)
        overall_status, warning_count, critical_count = self._derive_equipment_status(parameter_states)

        if previous_equipment_state is None:
            await self._equipment_state_repository.create(
                equipment=equipment,
                status=overall_status,
                warning_count=warning_count,
                critical_count=critical_count,
                last_evaluated_at=telemetry_reading.measured_at,
            )
        else:
            await self._equipment_state_repository.update(
                previous_equipment_state,
                status=overall_status,
                warning_count=warning_count,
                critical_count=critical_count,
                last_evaluated_at=telemetry_reading.measured_at,
            )

        await self._event_service.create_transition_events(
            equipment=equipment,
            parameter=parameter,
            telemetry_reading=telemetry_reading,
            previous_parameter_status=previous_parameter_status,
            new_parameter_status=status,
            previous_equipment_status=previous_equipment_status,
            new_equipment_status=overall_status,
        )

    async def list_equipment_states(self, *, status: str | None = None):
        """Return current equipment state snapshots."""

        if status is not None and status not in VALID_MONITORING_STATUSES:
            raise ValueError("Unsupported equipment status filter.")

        return await self._equipment_state_repository.list_all(status=status)

    async def get_equipment_state(self, equipment_id: UUID):
        """Return the aggregated current state snapshot of an equipment unit."""

        state = await self._equipment_state_repository.get_by_equipment_id(equipment_id)
        if state is None:
            return None, []

        parameter_states = await self._equipment_parameter_state_repository.list_by_equipment(equipment_id)
        return state, parameter_states

    @staticmethod
    def _calculate_metric_status(
        *,
        value: Decimal,
        warning_min: Decimal | None,
        warning_max: Decimal | None,
        critical_min: Decimal | None,
        critical_max: Decimal | None,
    ) -> str:
        """Calculate metric status for a reading value against threshold boundaries."""

        if critical_min is not None and value < critical_min:
            return METRIC_STATUS_CRITICAL
        if critical_max is not None and value > critical_max:
            return METRIC_STATUS_CRITICAL
        if warning_min is not None and value < warning_min:
            return METRIC_STATUS_WARNING
        if warning_max is not None and value > warning_max:
            return METRIC_STATUS_WARNING
        return METRIC_STATUS_NORMAL

    @staticmethod
    def _derive_equipment_status(parameter_states) -> tuple[str, int, int]:
        """Derive overall equipment status from current parameter statuses."""

        warning_count = sum(1 for state in parameter_states if state.status == METRIC_STATUS_WARNING)
        critical_count = sum(1 for state in parameter_states if state.status == METRIC_STATUS_CRITICAL)

        if critical_count > 0:
            return METRIC_STATUS_CRITICAL, warning_count, critical_count
        if warning_count > 0:
            return METRIC_STATUS_WARNING, warning_count, critical_count
        return METRIC_STATUS_NORMAL, warning_count, critical_count
