import uuid
from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def utc_now_aware() -> datetime:
    return datetime.now(UTC)


def generate_uuid() -> str:
    try:
        # uuid7 available in Python 3.13+
        return str(uuid.uuid7())  # type: ignore[attr-defined]
    except AttributeError:
        # Fallback for Python < 3.13
        return str(uuid.uuid4())
