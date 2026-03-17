from dataclasses import dataclass

from app.config.base import get_env


@dataclass(frozen=True)
class DatabaseConfig:
    """Database-related configuration values."""

    sqlalchemy_url: str | None = (
        get_env("SQLALCHEMY_URL")
        or get_env("SQLALCHEMY_URL_LOCAL")
        or get_env("SQLALCHEMY_URL_DOCKER")
    )
    sqlalchemy_url_local: str | None = get_env("SQLALCHEMY_URL_LOCAL")
    sqlalchemy_url_docker: str | None = get_env("SQLALCHEMY_URL_DOCKER")


db_config = DatabaseConfig()
