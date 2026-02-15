from datetime import UTC, datetime


def utc_now() -> datetime:
    """
    Get current UTC time as a naive datetime (no timezone info).

    This is required for PostgresSQL TIMESTAMP WITHOUT TIME ZONE columns
    which cannot accept timezone-aware datetime with asyncpg.

    Returns:
        Current UTC time as timezone-naive datetime
    """
    return datetime.now(UTC).replace(tzinfo=None)
