import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """Represents an application user with assigned roles."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    roles: Mapped[list["Role"]] = relationship(
        secondary="user_roles",
        back_populates="users",
    )
    created_maintenance_tasks: Mapped[list["MaintenanceTask"]] = relationship(
        foreign_keys="MaintenanceTask.created_by_user_id",
        back_populates="created_by_user",
    )
    assigned_maintenance_tasks: Mapped[list["MaintenanceTask"]] = relationship(
        foreign_keys="MaintenanceTask.assigned_to_user_id",
        back_populates="assigned_to_user",
    )
    performed_maintenance_records: Mapped[list["MaintenanceRecord"]] = relationship(
        back_populates="performed_by_user",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="recipient_user",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="actor_user",
    )
