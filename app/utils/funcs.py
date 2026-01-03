from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current date and time with a UTC timezone"""
    return datetime.now(tz=timezone.utc)
