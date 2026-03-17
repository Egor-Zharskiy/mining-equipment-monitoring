from dataclasses import dataclass

from app.config.base import get_env


@dataclass(frozen=True)
class AppConfig:
    """Application-level configuration values."""

    title: str = get_env("APP_TITLE", "Mining Equipment Monitoring API") or "Mining Equipment Monitoring API"
    api_v1_prefix: str = get_env("API_V1_PREFIX", "/api/v1") or "/api/v1"


app_config = AppConfig()
