from dataclasses import dataclass

from app.config.base import get_env, get_env_bool, get_env_int


@dataclass(frozen=True)
class MailConfig:
    """SMTP configuration for external email notification delivery."""

    enabled: bool = get_env_bool("MAIL_ENABLED", False)
    server: str | None = get_env("MAIL_SERVER") or get_env("SMTP_HOST")
    port: int = get_env_int("MAIL_PORT", get_env_int("SMTP_PORT", 587))
    username: str | None = get_env("MAIL_USERNAME") or get_env("SMTP_USERNAME")
    password: str | None = get_env("MAIL_PASSWORD") or get_env("SMTP_PASSWORD")
    from_email: str | None = (
        get_env("MAIL_FROM_EMAIL")
        or get_env("SMTP_FROM_EMAIL")
        or get_env("MAIL_USERNAME")
        or get_env("SMTP_USERNAME")
    )
    from_name: str = get_env("MAIL_FROM_NAME", "Mining Equipment Monitoring") or "Mining Equipment Monitoring"
    use_tls: bool = get_env_bool("MAIL_USE_TLS", get_env_bool("SMTP_USE_TLS", True))
    use_ssl: bool = get_env_bool("MAIL_USE_SSL", get_env_bool("SMTP_USE_SSL", False))
    timeout_seconds: int = get_env_int("MAIL_TIMEOUT_SECONDS", get_env_int("SMTP_TIMEOUT_SECONDS", 10))

    def validate_delivery_settings(self) -> None:
        """Validate required SMTP settings before sending an email."""

        missing_fields = []
        if not self.server:
            missing_fields.append("MAIL_SERVER")
        if not self.from_email:
            missing_fields.append("MAIL_FROM_EMAIL")
        if self.username and not self.password:
            missing_fields.append("MAIL_PASSWORD")
        if self.password and not self.username:
            missing_fields.append("MAIL_USERNAME")
        if self.use_tls and self.use_ssl:
            raise ValueError("MAIL_USE_TLS and MAIL_USE_SSL cannot both be enabled.")
        if missing_fields:
            raise ValueError(f"Missing SMTP settings: {', '.join(missing_fields)}.")


mail_config = MailConfig()
