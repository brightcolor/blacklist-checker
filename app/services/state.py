from datetime import datetime, timezone

from app.models.monitor import CheckRun


def summarize_diff(previous: CheckRun | None, listed_count: int, error_count: int) -> str | None:
    if previous is None:
        return None
    parts: list[str] = []
    if listed_count > previous.listed_count:
        parts.append("more_listings")
    if listed_count < previous.listed_count:
        parts.append("removed_listing")
    if error_count > previous.error_count:
        parts.append("more_errors")
    if error_count < previous.error_count:
        parts.append("fewer_errors")
    return ",".join(parts) if parts else None


def utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)
