"""Backward-compatible model import module."""

from app.models import Equipment, EquipmentType, Permission, Role, RolePermission, User, UserRole

__all__ = [
    "Equipment",
    "EquipmentType",
    "Permission",
    "Role",
    "RolePermission",
    "User",
    "UserRole",
]
