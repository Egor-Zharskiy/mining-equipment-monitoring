from dataclasses import dataclass, field

from app.config.base import get_env, get_env_bool, get_env_list


@dataclass(frozen=True)
class AppConfig:
    """Application-level configuration values."""

    title: str = get_env("APP_TITLE", "Mining Equipment Monitoring API") or "Mining Equipment Monitoring API"
    api_v1_prefix: str = get_env("API_V1_PREFIX", "/api/v1") or "/api/v1"
    runtime_notifications_enabled: bool = get_env_bool("ENABLE_RUNTIME_NOTIFICATIONS", True)
    auth_profiling_enabled: bool = get_env_bool("ENABLE_AUTH_PROFILING", False)
    log_level: str = get_env("LOG_LEVEL", "INFO") or "INFO"
    log_format: str = get_env("LOG_FORMAT", "plain") or "plain"
    log_requests_enabled: bool = get_env_bool("LOG_REQUESTS", True)
    cors_allow_origins: list[str] = field(
        default_factory=lambda: get_env_list(
            "CORS_ALLOW_ORIGINS",
            ["http://localhost:5173", "http://127.0.0.1:5173"],
        )
    )
    cors_allow_origin_regex: str = (
        get_env(
            "CORS_ALLOW_ORIGIN_REGEX",
            r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$",
        )
        or r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$"
    )


app_config = AppConfig()
