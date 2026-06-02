from app.models.monitor import CheckRun, MonitorStatus, TargetType
from app.services.state import summarize_diff


def make_run(listed: int, errors: int) -> CheckRun:
    run = CheckRun(
        target_type=TargetType.IPV4,
        target_value="203.0.113.1",
        overall_status=MonitorStatus.OK,
        listed_count=listed,
        error_count=errors,
        degraded_count=errors,
        duration_ms=5,
    )
    return run


def test_summarize_diff_more_listings():
    previous = make_run(0, 0)
    assert summarize_diff(previous, 1, 0) == "more_listings"


def test_summarize_diff_multiple():
    previous = make_run(2, 2)
    out = summarize_diff(previous, 1, 3)
    assert out == "removed_listing,more_errors"
