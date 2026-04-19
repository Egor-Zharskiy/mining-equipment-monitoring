from fastapi import APIRouter

from app.api.v1.endpoints.audit_logs import router as audit_logs_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.equipment import router as equipment_router
from app.api.v1.endpoints.equipment_states import router as equipment_states_router
from app.api.v1.endpoints.equipment_type_parameters import router as equipment_type_parameters_router
from app.api.v1.endpoints.equipment_types import router as equipment_types_router
from app.api.v1.endpoints.events import router as events_router
from app.api.v1.endpoints.maintenance_plans import router as maintenance_plans_router
from app.api.v1.endpoints.maintenance_records import router as maintenance_records_router
from app.api.v1.endpoints.maintenance_tasks import router as maintenance_tasks_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.parameters import router as parameters_router
from app.api.v1.endpoints.permissions import router as permissions_router
from app.api.v1.endpoints.roles import router as roles_router
from app.api.v1.endpoints.search import router as search_router
from app.api.v1.endpoints.telemetry_readings import router as telemetry_readings_router
from app.api.v1.endpoints.threshold_rules import router as threshold_rules_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(analytics_router)
api_router.include_router(audit_logs_router)
api_router.include_router(search_router)
api_router.include_router(equipment_types_router)
api_router.include_router(equipment_router)
api_router.include_router(equipment_states_router)
api_router.include_router(events_router)
api_router.include_router(maintenance_plans_router)
api_router.include_router(maintenance_tasks_router)
api_router.include_router(maintenance_records_router)
api_router.include_router(notifications_router)
api_router.include_router(parameters_router)
api_router.include_router(equipment_type_parameters_router)
api_router.include_router(threshold_rules_router)
api_router.include_router(telemetry_readings_router)
api_router.include_router(permissions_router)
api_router.include_router(roles_router)
api_router.include_router(users_router)
