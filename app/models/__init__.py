"""ORM model exports for metadata registration."""

from app.models.audit_log import AuditLog
from app.models.equipment import Equipment
from app.models.equipment_parameter_state import EquipmentParameterState
from app.models.equipment_state import EquipmentState
from app.models.event import Event
from app.models.equipment_type import EquipmentType
from app.models.equipment_type_parameter import EquipmentTypeParameter
from app.models.maintenance_plan import MaintenancePlan
from app.models.maintenance_record import MaintenanceRecord
from app.models.maintenance_task import MaintenanceTask
from app.models.notification import Notification
from app.models.parameter import Parameter
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.telemetry_evaluation import TelemetryEvaluation
from app.models.telemetry_reading import TelemetryReading
from app.models.threshold_rule import ThresholdRule
from app.models.user import User
from app.models.user_role import UserRole

__all__ = [
    "AuditLog",
    "Equipment",
    "EquipmentParameterState",
    "EquipmentState",
    "Event",
    "EquipmentType",
    "EquipmentTypeParameter",
    "MaintenancePlan",
    "MaintenanceRecord",
    "MaintenanceTask",
    "Notification",
    "Parameter",
    "Permission",
    "Role",
    "RolePermission",
    "TelemetryEvaluation",
    "TelemetryReading",
    "ThresholdRule",
    "User",
    "UserRole",
]
