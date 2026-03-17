"""normalize default admin user

Revision ID: 25a207d82315
Revises: cf33ec53da34
Create Date: 2026-03-17 00:35:52.015120

"""
import base64
import hashlib
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '25a207d82315'
down_revision: Union[str, Sequence[str], None] = 'cf33ec53da34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ADMIN_ROLE_ID = uuid.UUID("c2b7db50-e043-4592-9a08-995545274001")


def _hash_password(password: str) -> str:
    salt = bytes.fromhex("3f5a2a9b0c4e6d8f1a2b3c4d5e6f7081")
    derived_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{base64.b64encode(salt).decode()}${base64.b64encode(derived_key).decode()}"


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        sa.text(
            """
            INSERT INTO users (id, username, email, hashed_password, first_name, last_name, is_active)
            SELECT :id, :username, :email, :hashed_password, :first_name, :last_name, :is_active
            WHERE NOT EXISTS (
                SELECT 1 FROM users WHERE username = :username OR email = :email
            )
            """
        ).bindparams(
            id=uuid.UUID("66ea84f4-d2f8-4532-a566-5cd20a640001"),
            username="admin",
            email="admin@example.com",
            hashed_password=_hash_password("Admin123!"),
            first_name="System",
            last_name="Administrator",
            is_active=True,
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE users
            SET email = :email,
                hashed_password = :hashed_password,
                first_name = :first_name,
                last_name = :last_name,
                is_active = :is_active
            WHERE username = :username
            """
        ).bindparams(
            username="admin",
            email="admin@example.com",
            hashed_password=_hash_password("Admin123!"),
            first_name="System",
            last_name="Administrator",
            is_active=True,
        )
    )

    op.execute(
        sa.text(
            """
            INSERT INTO user_roles (id, user_id, role_id)
            SELECT :id, users.id, :role_id
            FROM users
            WHERE users.username = :username
              AND NOT EXISTS (
                  SELECT 1
                  FROM user_roles
                  WHERE user_roles.user_id = users.id AND user_roles.role_id = :role_id
              )
            """
        ).bindparams(
            id=uuid.UUID("d4cb804f-2f4a-4f4f-ac3f-e6520dc64001"),
            username="admin",
            role_id=ADMIN_ROLE_ID,
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text(
            """
            DELETE FROM user_roles
            WHERE role_id = :role_id
              AND user_id IN (SELECT id FROM users WHERE username = :username)
            """
        ).bindparams(role_id=ADMIN_ROLE_ID, username="admin")
    )
