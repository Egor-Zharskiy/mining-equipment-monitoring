from decimal import Decimal
from uuid import UUID

from app.repositories.equipment_type_parameter_repository import EquipmentTypeParameterRepository
from app.repositories.equipment_type_repository import EquipmentTypeRepository
from app.repositories.parameter_repository import ParameterRepository
from app.repositories.threshold_rule_repository import ThresholdRuleRepository, UNSET
from app.schemas.threshold_rule import ThresholdRuleCreate, ThresholdRuleUpdate


class ThresholdRuleService:
    """Encapsulates business rules for threshold rules."""

    def __init__(
        self,
        threshold_rule_repository: ThresholdRuleRepository,
        equipment_type_repository: EquipmentTypeRepository,
        parameter_repository: ParameterRepository,
        equipment_type_parameter_repository: EquipmentTypeParameterRepository,
    ) -> None:
        """Store repository dependencies used by the service."""

        self._threshold_rule_repository = threshold_rule_repository
        self._equipment_type_repository = equipment_type_repository
        self._parameter_repository = parameter_repository
        self._equipment_type_parameter_repository = equipment_type_parameter_repository

    async def create_threshold_rule(self, payload: ThresholdRuleCreate):
        """Create a new threshold rule for an equipment type parameter pair."""

        equipment_type = await self._equipment_type_repository.get_by_id(payload.equipment_type_id)
        if equipment_type is None:
            raise ValueError("Equipment type was not found.")

        parameter = await self._parameter_repository.get_by_id(payload.parameter_id)
        if parameter is None:
            raise ValueError("Parameter was not found.")

        await self._ensure_binding_exists(payload.equipment_type_id, payload.parameter_id)

        existing_rule = await self._threshold_rule_repository.get_by_equipment_type_and_parameter(
            equipment_type_id=payload.equipment_type_id,
            parameter_id=payload.parameter_id,
        )
        if existing_rule is not None:
            raise ValueError("Threshold rule for this equipment type and parameter already exists.")

        self._validate_thresholds(
            warning_min=payload.warning_min,
            warning_max=payload.warning_max,
            critical_min=payload.critical_min,
            critical_max=payload.critical_max,
        )

        return await self._threshold_rule_repository.create(
            equipment_type=equipment_type,
            parameter=parameter,
            warning_min=payload.warning_min,
            warning_max=payload.warning_max,
            critical_min=payload.critical_min,
            critical_max=payload.critical_max,
            is_active=payload.is_active,
        )

    async def list_threshold_rules(
        self,
        *,
        equipment_type_id: UUID | None = None,
        parameter_id: UUID | None = None,
    ):
        """Return threshold rules optionally filtered by equipment type or parameter."""

        return await self._threshold_rule_repository.list_all(
            equipment_type_id=equipment_type_id,
            parameter_id=parameter_id,
        )

    async def get_threshold_rule(self, rule_id: UUID):
        """Return a threshold rule by identifier."""

        return await self._threshold_rule_repository.get_by_id(rule_id)

    async def update_threshold_rule(self, rule_id: UUID, payload: ThresholdRuleUpdate):
        """Update an existing threshold rule."""

        rule = await self._threshold_rule_repository.get_by_id(rule_id)
        if rule is None:
            return None

        update_data = payload.model_dump(exclude_unset=True)

        final_equipment_type_id = update_data.get("equipment_type_id", rule.equipment_type_id)
        final_parameter_id = update_data.get("parameter_id", rule.parameter_id)
        final_warning_min = update_data.get("warning_min", rule.warning_min)
        final_warning_max = update_data.get("warning_max", rule.warning_max)
        final_critical_min = update_data.get("critical_min", rule.critical_min)
        final_critical_max = update_data.get("critical_max", rule.critical_max)

        equipment_type = rule.equipment_type
        if "equipment_type_id" in update_data:
            equipment_type = await self._equipment_type_repository.get_by_id(final_equipment_type_id)
            if equipment_type is None:
                raise ValueError("Equipment type was not found.")

        parameter = rule.parameter
        if "parameter_id" in update_data:
            parameter = await self._parameter_repository.get_by_id(final_parameter_id)
            if parameter is None:
                raise ValueError("Parameter was not found.")

        if (
            final_equipment_type_id != rule.equipment_type_id
            or final_parameter_id != rule.parameter_id
        ):
            await self._ensure_binding_exists(final_equipment_type_id, final_parameter_id)

            existing_rule = await self._threshold_rule_repository.get_by_equipment_type_and_parameter(
                equipment_type_id=final_equipment_type_id,
                parameter_id=final_parameter_id,
            )
            if existing_rule is not None and existing_rule.id != rule.id:
                raise ValueError("Threshold rule for this equipment type and parameter already exists.")

        self._validate_thresholds(
            warning_min=final_warning_min,
            warning_max=final_warning_max,
            critical_min=final_critical_min,
            critical_max=final_critical_max,
        )

        return await self._threshold_rule_repository.update(
            rule,
            equipment_type=equipment_type if "equipment_type_id" in update_data else UNSET,
            parameter=parameter if "parameter_id" in update_data else UNSET,
            warning_min=update_data["warning_min"] if "warning_min" in update_data else UNSET,
            warning_max=update_data["warning_max"] if "warning_max" in update_data else UNSET,
            critical_min=update_data["critical_min"] if "critical_min" in update_data else UNSET,
            critical_max=update_data["critical_max"] if "critical_max" in update_data else UNSET,
            is_active=update_data["is_active"] if "is_active" in update_data else UNSET,
        )

    async def delete_threshold_rule(self, rule_id: UUID):
        """Delete a threshold rule by identifier."""

        rule = await self._threshold_rule_repository.get_by_id(rule_id)
        if rule is None:
            return None

        await self._threshold_rule_repository.delete(rule)
        return rule

    async def _ensure_binding_exists(self, equipment_type_id: UUID, parameter_id: UUID) -> None:
        """Validate that the parameter is assigned to the equipment type."""

        binding = await self._equipment_type_parameter_repository.get_by_equipment_type_and_parameter(
            equipment_type_id=equipment_type_id,
            parameter_id=parameter_id,
        )
        if binding is None:
            raise ValueError("Threshold rule requires an existing equipment type parameter binding.")

    @staticmethod
    def _validate_thresholds(
        *,
        warning_min: Decimal | None,
        warning_max: Decimal | None,
        critical_min: Decimal | None,
        critical_max: Decimal | None,
    ) -> None:
        """Validate threshold consistency rules."""

        if all(value is None for value in (warning_min, warning_max, critical_min, critical_max)):
            raise ValueError("At least one threshold value must be provided.")

        if warning_min is not None and warning_max is not None and warning_min > warning_max:
            raise ValueError("warning_min must be less than or equal to warning_max.")

        if critical_min is not None and critical_max is not None and critical_min > critical_max:
            raise ValueError("critical_min must be less than or equal to critical_max.")

        if critical_min is not None and warning_min is not None and critical_min > warning_min:
            raise ValueError("critical_min must be less than or equal to warning_min.")

        if warning_max is not None and critical_max is not None and warning_max > critical_max:
            raise ValueError("warning_max must be less than or equal to critical_max.")
