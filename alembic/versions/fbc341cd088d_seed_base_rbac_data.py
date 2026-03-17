"""seed base rbac data

Revision ID: fbc341cd088d
Revises: 61f323a49087
Create Date: 2026-03-17 00:16:56.383430

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fbc341cd088d"
down_revision: Union[str, Sequence[str], None] = "61f323a49087"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

permissions_table = sa.table(
    "permissions",
    sa.column("id", sa.UUID()),
    sa.column("code", sa.String()),
    sa.column("description", sa.String()),
)

roles_table = sa.table(
    "roles",
    sa.column("id", sa.UUID()),
    sa.column("name", sa.String()),
    sa.column("description", sa.String()),
)

role_permissions_table = sa.table(
    "role_permissions",
    sa.column("id", sa.UUID()),
    sa.column("role_id", sa.UUID()),
    sa.column("permission_id", sa.UUID()),
)

PERMISSIONS = {
    "users.read": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f001"),
        "description": "Read user accounts.",
    },
    "users.create": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f002"),
        "description": "Create user accounts.",
    },
    "users.update": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f003"),
        "description": "Update user accounts.",
    },
    "users.delete": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f004"),
        "description": "Delete user accounts.",
    },
    "roles.read": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f005"),
        "description": "Read role definitions.",
    },
    "roles.manage": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f006"),
        "description": "Create and update role definitions.",
    },
    "permissions.read": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f007"),
        "description": "Read permission catalog.",
    },
    "equipment.read": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f008"),
        "description": "Read equipment data.",
    },
    "equipment.manage": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f009"),
        "description": "Create and update equipment data.",
    },
    "telemetry.read": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f00a"),
        "description": "Read telemetry history.",
    },
    "telemetry.create": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f00b"),
        "description": "Submit telemetry readings.",
    },
    "events.read": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f00c"),
        "description": "Read equipment events.",
    },
    "events.manage": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f00d"),
        "description": "Create and update equipment events.",
    },
    "maintenance.read": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f00e"),
        "description": "Read maintenance plans and records.",
    },
    "maintenance.manage": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f00f"),
        "description": "Create and update maintenance plans and records.",
    },
    "notifications.read": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f010"),
        "description": "Read notifications.",
    },
    "notifications.manage": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f011"),
        "description": "Create and manage notifications.",
    },
    "analytics.read": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f012"),
        "description": "Read analytics and dashboards.",
    },
    "audit.read": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f013"),
        "description": "Read audit logs.",
    },
}

ROLES = {
    "admin": {
        "id": uuid.UUID("c2b7db50-e043-4592-9a08-995545274001"),
        "description": "System administrator with full platform access.",
        "permissions": list(PERMISSIONS.keys()),
    },
    "manager": {
        "id": uuid.UUID("c2b7db50-e043-4592-9a08-995545274002"),
        "description": "Management role focused on monitoring, analytics, and oversight.",
        "permissions": [
            "users.read",
            "roles.read",
            "permissions.read",
            "equipment.read",
            "telemetry.read",
            "events.read",
            "maintenance.read",
            "notifications.read",
            "analytics.read",
            "audit.read",
        ],
    },
    "technician": {
        "id": uuid.UUID("c2b7db50-e043-4592-9a08-995545274003"),
        "description": "Operational role focused on telemetry, events, and maintenance work.",
        "permissions": [
            "equipment.read",
            "telemetry.read",
            "telemetry.create",
            "events.read",
            "events.manage",
            "maintenance.read",
            "maintenance.manage",
            "notifications.read",
        ],
    },
}


def upgrade() -> None:
    """Upgrade schema."""

    op.bulk_insert(
        permissions_table,
        [
            {
                "id": permission["id"],
                "code": code,
                "description": permission["description"],
            }
            for code, permission in PERMISSIONS.items()
        ],
    )

    op.bulk_insert(
        roles_table,
        [
            {
                "id": role["id"],
                "name": name,
                "description": role["description"],
            }
            for name, role in ROLES.items()
        ],
    )

    role_permission_rows: list[dict[str, object]] = []
    for role in ROLES.values():
        for permission_code in role["permissions"]:
            role_permission_rows.append(
                {
                    "id": uuid.uuid4(),
                    "role_id": role["id"],
                    "permission_id": PERMISSIONS[permission_code]["id"],
                }
            )

    op.bulk_insert(role_permissions_table, role_permission_rows)


def downgrade() -> None:
    """Downgrade schema."""

    role_ids = [role["id"] for role in ROLES.values()]
    permission_ids = [permission["id"] for permission in PERMISSIONS.values()]

    op.execute(
        sa.delete(role_permissions_table).where(
            role_permissions_table.c.role_id.in_(role_ids)
        )
    )
    op.execute(sa.delete(roles_table).where(roles_table.c.id.in_(role_ids)))
    op.execute(
        sa.delete(permissions_table).where(
            permissions_table.c.id.in_(permission_ids)
        )
    )
