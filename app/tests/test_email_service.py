import pytest

from app.config.mail_config import MailConfig
from app.services.email_service import EmailDeliveryError, EmailService


class FakeSMTP:
    """Small SMTP test double that records delivery calls."""

    instances = []

    def __init__(self, server, port, timeout):
        self.server = server
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.login_args = None
        self.sent_messages = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, username, password):
        self.login_args = (username, password)

    def send_message(self, message, to_addrs):
        self.sent_messages.append((message, to_addrs))


@pytest.mark.asyncio
async def test_email_service_returns_false_when_delivery_is_disabled(monkeypatch):
    monkeypatch.setattr(
        "app.services.email_service.smtplib.SMTP",
        lambda *args, **kwargs: pytest.fail("SMTP should not be opened when mail is disabled."),
    )

    service = EmailService(
        MailConfig(
            enabled=False,
            server="smtp.example.com",
            port=587,
            username="sender@example.com",
            password="secret",
            from_email="sender@example.com",
            from_name="MEM",
            use_tls=True,
            use_ssl=False,
            timeout_seconds=5,
        )
    )

    delivered = await service.send_email(
        to_email="recipient@example.com",
        subject="Тестовое уведомление",
        body="Проверка доставки.",
    )

    assert delivered is False


@pytest.mark.asyncio
async def test_email_service_sends_message_with_starttls(monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr("app.services.email_service.smtplib.SMTP", FakeSMTP)

    service = EmailService(
        MailConfig(
            enabled=True,
            server="smtp.example.com",
            port=587,
            username="sender@example.com",
            password="secret",
            from_email="sender@example.com",
            from_name="Mining Equipment Monitoring",
            use_tls=True,
            use_ssl=False,
            timeout_seconds=5,
        )
    )

    delivered = await service.send_email(
        to_email="recipient@example.com",
        subject="Критическое событие",
        body="Параметр вышел за критический порог.",
    )

    assert delivered is True
    smtp = FakeSMTP.instances[0]
    assert smtp.server == "smtp.example.com"
    assert smtp.port == 587
    assert smtp.timeout == 5
    assert smtp.started_tls is True
    assert smtp.login_args == ("sender@example.com", "secret")
    message, to_addrs = smtp.sent_messages[0]
    assert message["Subject"] == "Критическое событие"
    assert message["To"] == "recipient@example.com"
    assert to_addrs == ["recipient@example.com"]


@pytest.mark.asyncio
async def test_email_service_sanitizes_unicode_headers(monkeypatch):
    FakeSMTP.instances = []
    monkeypatch.setattr("app.services.email_service.smtplib.SMTP", FakeSMTP)

    service = EmailService(
        MailConfig(
            enabled=True,
            server="smtp.example.com",
            port=587,
            username="sender@example.com",
            password="secret",
            from_email="sender@example.com",
            from_name="Система мониторинга горного оборудования",
            use_tls=True,
            use_ssl=False,
            timeout_seconds=5,
        )
    )

    delivered = await service.send_email(
        to_email="recipient@example.com",
        subject="Автоматическая проверка email уведомления\nBcc: hidden@example.com",
        body="Задача создана для проверки автоматической SMTP-доставки.",
    )

    assert delivered is True
    message, _ = FakeSMTP.instances[0].sent_messages[0]
    assert "\n" not in message["Subject"]
    assert "\r" not in message["Subject"]
    assert "Автоматическая проверка email уведомления Bcc: hidden@example.com" == message["Subject"]
    assert "\n" not in message["From"]
    assert "\r" not in message["From"]
    message.as_string()


@pytest.mark.asyncio
async def test_email_service_rejects_missing_required_settings():
    service = EmailService(
        MailConfig(
            enabled=True,
            server=None,
            port=587,
            username=None,
            password=None,
            from_email=None,
            from_name="MEM",
            use_tls=True,
            use_ssl=False,
            timeout_seconds=5,
        )
    )

    with pytest.raises(EmailDeliveryError, match="Missing SMTP settings"):
        await service.send_email(
            to_email="recipient@example.com",
            subject="Уведомление",
            body="Сообщение.",
        )
