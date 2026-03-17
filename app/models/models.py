"""Backward-compatible model import module."""

from app.models import Permission, Role, RolePermission, User, UserRole

__all__ = [
    "Permission",
    "Role",
    "RolePermission",
    "User",
    "UserRole",
]
