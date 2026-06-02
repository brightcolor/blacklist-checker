import asyncio
from datetime import datetime, timedelta, timezone

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import or_, select

from app.db.session import SessionLocal
from app.models.monitor import Monitor
from app.services.alerts import AlertDispatcher
from app.services.check_service import CheckService

logger = structlog.get_logger(__name__)

check_service = CheckService()
alert_dispatcher = AlertDispatcher()


async def run_due_monitors() -> None:
    now = datetime.now(tz=timezone.utc)
    db = SessionLocal()
    try:
        monitors = (
            db.execute(
                select(Monitor).where(
                    Monitor.is_enabled.is_(True),
                    Monitor.maintenance_mode.is_(False),
                    or_(Monitor.next_run_at.is_(None), Monitor.next_run_at <= now),
                )
            )
            .scalars()
            .all()
        )

        for monitor in monitors:
            try:
                run = await check_service.run_monitor_check(db, monitor)
                await alert_dispatcher.dispatch_monitor_events(db, monitor, run)
            except Exception:
                logger.exception("monitor_check_failed", monitor_id=monitor.id)
                monitor.next_run_at = now + timedelta(minutes=monitor.interval_minutes)
                db.commit()
    finally:
        db.close()


async def startup() -> None:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(run_due_monitors, "interval", seconds=30, max_instances=1, coalesce=True)
    scheduler.start()
    logger.info("worker_started")
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(startup())
