"""seed threshold rule permissions

Revision ID: 8c0c7d8e9f41
Revises: 52d7570d1f86
Create Date: 2026-03-23 00:05:00.000000

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c0c7d8e9f41"
down_revision: Union[str, Sequence[str], None] = "52d7570d1f86"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ADMIN_ROLE_ID = uuid.UUID("c2b7db50-e043-4592-9a08-995545274001")
MANAGER_ROLE_ID = uuid.UUID("c2b7db50-e043-4592-9a08-995545274002")

THRESHOLD_RULE_PERMISSIONS = {
    "threshold_rules.read": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f014"),
        "description": "Read threshold rules.",
    },
    "threshold_rules.manage": {
        "id": uuid.UUID("b7af4a2b-1a11-43db-9e06-cb597494f015"),
        "description": "Create, update, and delete threshold rules.",
    },
}

permissions_table = sa.table(
    "permissions",
    sa.column("id", sa.UUID()),
)

role_permissions_table = sa.table(
    "role_permissions",
    sa.column("permission_id", sa.UUID()),
)

ROLE_ASSIGNMENTS = {
    ADMIN_ROLE_ID: [
        THRESHOLD_RULE_PERMISSIONS["threshold_rules.read"]["id"],
        THRESHOLD_RULE_PERMISSIONS["threshold_rules.manage"]["id"],
    ],
    MANAGER_ROLE_ID: [
        THRESHOLD_RULE_PERMISSIONS["threshold_rules.read"]["id"],
    ],
}


def upgrade() -> None:
    """Upgrade schema."""

    for code, permission in THRESHOLD_RULE_PERMISSIONS.items():
        op.execute(
            sa.text(
                """
                INSERT INTO permissions (id, code, description)
                SELECT :id, :code, :description
                WHERE NOT EXISTS (
                    SELECT 1 FROM permissions WHERE code = :code
                )
                """
            ).bindparams(
                id=permission["id"],
                code=code,
                description=permission["description"],
            )
        )

    for role_id, permission_ids in ROLE_ASSIGNMENTS.items():
        for permission_id in permission_ids:
            op.execute(
                sa.text(
                    """
                    INSERT INTO role_permissions (id, role_id, permission_id)
                    SELECT :id, :role_id, :permission_id
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM role_permissions
                        WHERE role_id = :role_id AND permission_id = :permission_id
                    )
                    """
                ).bindparams(
                    id=uuid.uuid4(),
                    role_id=role_id,
                    permission_id=permission_id,
                )
            )


def downgrade() -> None:
    """Downgrade schema."""

    permission_ids = [permission["id"] for permission in THRESHOLD_RULE_PERMISSIONS.values()]

    op.execute(
        sa.delete(role_permissions_table).where(role_permissions_table.c.permission_id.in_(permission_ids))
    )
    op.execute(sa.delete(permissions_table).where(permissions_table.c.id.in_(permission_ids)))
