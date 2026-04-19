import logging
import time
from contextlib import contextmanager

from app.config import app_config

logger = logging.getLogger("app.auth_profiling")


def is_auth_profiling_enabled() -> bool:
    """Return whether lightweight auth profiling logs are enabled."""

    return app_config.auth_profiling_enabled


def log_auth_profile(step: str, duration: float, **details) -> None:
    """Emit a structured auth profiling log entry when profiling is enabled."""

    if not is_auth_profiling_enabled():
        return

    suffix = " ".join(f"{key}={value}" for key, value in details.items() if value is not None)
    message = f"[auth-profile] {step} took={duration:.6f}s"
    if suffix:
        message = f"{message} {suffix}"
    logger.warning(message)


@contextmanager
def profile_auth_step(step: str, **details):
    """Profile a synchronous block in the auth path."""

    start = time.perf_counter()
    try:
        yield
    finally:
        log_auth_profile(step, time.perf_counter() - start, **details)
