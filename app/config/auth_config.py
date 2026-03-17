from dataclasses import dataclass

from app.config.base import get_env


@dataclass(frozen=True)
class AuthConfig:
    """Authentication-related configuration values."""

    secret_key: str = get_env("AUTH_SECRET_KEY", "change-me-in-production") or "change-me-in-production"
    algorithm: str = get_env("AUTH_ALGORITHM", "HS256") or "HS256"
    access_token_expire_minutes: int = int(
        get_env("AUTH_ACCESS_TOKEN_EXPIRE_MINUTES", "60") or "60"
    )


auth_config = AuthConfig()
