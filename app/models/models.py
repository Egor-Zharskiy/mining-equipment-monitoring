"""Backward-compatible model import module."""

from app.models import (
    Equipment,
    EquipmentType,
    EquipmentTypeParameter,
    Parameter,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)

__all__ = [
    "Equipment",
    "EquipmentType",
    "EquipmentTypeParameter",
    "Parameter",
    "Permission",
    "Role",
    "RolePermission",
    "User",
    "UserRole",
]
