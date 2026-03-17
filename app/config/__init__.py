"""Project configuration entry points."""

from app.config.app_config import app_config
from app.config.auth_config import auth_config
from app.config.db_config import db_config

__all__ = [
    "app_config",
    "auth_config",
    "db_config",
]
