import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def get_env(name: str, default: str | None = None) -> str | None:
    """Return an environment variable loaded from the project dotenv file."""

    return os.getenv(name, default)
