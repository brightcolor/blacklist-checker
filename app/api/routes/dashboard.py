from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.deps import get_db
from app.models.monitor import CheckRun, Monitor, MonitorStatus
from app.models.user import AlertEvent, User
from app.schemas.api import DashboardOut

router = APIRouter()


@router.get("", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> DashboardOut:
    now = datetime.now(tz=timezone.utc)
    day_ago = now - timedelta(days=1)

    monitors_total = db.execute(select(func.count()).select_from(Monitor).where(Monitor.user_id == user.id)).scalar_one()
    currently_listed = db.execute(
        select(func.count()).select_from(Monitor).where(Monitor.user_id == user.id, Monitor.last_status == MonitorStatus.LISTED)
    ).scalar_one()
    new_listings_today = db.execute(
        select(func.count()).select_from(CheckRun).where(
            CheckRun.user_id == user.id,
            CheckRun.run_at >= day_ago,
            CheckRun.diff_summary.like("%more_listings%"),
        )
    ).scalar_one()
    failed_checks_last_24h = db.execute(
        select(func.count()).select_from(CheckRun).where(
            CheckRun.user_id == user.id,
            CheckRun.run_at >= day_ago,
            CheckRun.error_count > 0,
        )
    ).scalar_one()
    alerts_last_24h = db.execute(
        select(func.count()).select_from(AlertEvent).where(AlertEvent.user_id == user.id, AlertEvent.created_at >= day_ago)
    ).scalar_one()

    return DashboardOut(
        monitors_total=monitors_total,
        currently_listed=currently_listed,
        new_listings_today=new_listings_today,
        failed_checks_last_24h=failed_checks_last_24h,
        alerts_last_24h=alerts_last_24h,
    )
