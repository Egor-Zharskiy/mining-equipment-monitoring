import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def get_env(name: str, default: str | None = None) -> str | None:
    """Return an environment variable loaded from the project dotenv file."""

    return os.getenv(name, default)


def get_env_bool(name: str, default: bool = False) -> bool:
    """Return an environment variable parsed as a boolean."""

    value = get_env(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_env_int(name: str, default: int) -> int:
    """Return an environment variable parsed as an integer."""

    value = get_env(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def get_env_list(name: str, default: list[str] | None = None) -> list[str]:
    """Return a comma-separated environment variable as a list."""

    value = get_env(name)
    if value is None:
        return list(default or [])

    return [item.strip() for item in value.split(",") if item.strip()]
