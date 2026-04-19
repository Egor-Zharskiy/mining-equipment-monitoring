import asyncio
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.config import mail_config
from app.config.mail_config import MailConfig


class EmailDeliveryError(RuntimeError):
    """Raised when SMTP delivery fails or is misconfigured."""


class EmailService:
    """Sends external email notifications through SMTP."""

    def __init__(self, config: MailConfig | None = None) -> None:
        self._config = config or mail_config

    async def send_email(self, *, to_email: str, subject: str, body: str) -> bool:
        """Send a plain-text email if mail delivery is enabled."""

        if not self._config.enabled:
            return False

        try:
            self._config.validate_delivery_settings()
        except ValueError as error:
            raise EmailDeliveryError(str(error)) from error

        try:
            message = self._build_message(to_email=to_email, subject=subject, body=body)
            await asyncio.to_thread(self._send_message, to_email, message)
        except (OSError, smtplib.SMTPException, ValueError) as error:
            raise EmailDeliveryError("SMTP email delivery failed.") from error

        return True

    def _build_message(self, *, to_email: str, subject: str, body: str) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = self._sanitize_header(subject)
        message["From"] = formataddr(
            (
                self._sanitize_header(self._config.from_name),
                self._config.from_email or "",
            ),
            charset="utf-8",
        )
        message["To"] = self._sanitize_header(to_email)
        message.set_content(body, charset="utf-8")
        return message

    def _send_message(self, to_email: str, message: EmailMessage) -> None:
        if self._config.use_ssl:
            with smtplib.SMTP_SSL(
                self._config.server,
                self._config.port,
                timeout=self._config.timeout_seconds,
            ) as smtp:
                self._login_if_needed(smtp)
                smtp.send_message(message, to_addrs=[to_email])
            return

        with smtplib.SMTP(
            self._config.server,
            self._config.port,
            timeout=self._config.timeout_seconds,
        ) as smtp:
            if self._config.use_tls:
                smtp.starttls()
            self._login_if_needed(smtp)
            smtp.send_message(message, to_addrs=[to_email])

    def _login_if_needed(self, smtp) -> None:
        if self._config.username and self._config.password:
            smtp.login(self._config.username, self._config.password)

    @staticmethod
    def _sanitize_header(value: str) -> str:
        return " ".join(str(value).splitlines())
