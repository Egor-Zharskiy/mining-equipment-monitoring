from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.equipment import router as equipment_router
from app.api.v1.endpoints.equipment_type_parameters import router as equipment_type_parameters_router
from app.api.v1.endpoints.equipment_types import router as equipment_types_router
from app.api.v1.endpoints.parameters import router as parameters_router
from app.api.v1.endpoints.permissions import router as permissions_router
from app.api.v1.endpoints.roles import router as roles_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(equipment_types_router)
api_router.include_router(equipment_router)
api_router.include_router(parameters_router)
api_router.include_router(equipment_type_parameters_router)
api_router.include_router(permissions_router)
api_router.include_router(roles_router)
api_router.include_router(users_router)
