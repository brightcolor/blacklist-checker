import asyncio
import time
from collections.abc import Sequence

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.monitor import CheckRun, CheckRunResult, CheckStatus, Monitor, MonitorStatus, TargetType
from app.models.rbl import RBLList
from app.services.csv_utils import from_csv_int, to_csv_int
from app.services.dns_engine import DNSLookupEngine, DNSCheckOutcome
from app.services.state import summarize_diff, utcnow

settings = get_settings()


class CheckService:
    def __init__(self) -> None:
        self.engine = DNSLookupEngine()
        self.semaphore = asyncio.Semaphore(settings.dns_max_concurrency)

    async def run_manual_check(
        self,
        db: Session,
        target_type: TargetType,
        target_value: str,
        list_ids: list[int] | None,
        user_id: int | None,
    ) -> CheckRun:
        lists = self._resolve_lists(db, target_type, list_ids)
        return await self._run(db, None, user_id, target_type, target_value, lists)

    async def run_monitor_check(self, db: Session, monitor: Monitor) -> CheckRun:
        list_ids = from_csv_int(monitor.list_ids_csv)
        lists = self._resolve_lists(db, monitor.target_type, list_ids)
        return await self._run(db, monitor.id, monitor.user_id, monitor.target_type, monitor.target_value, lists)

    def _resolve_lists(
        self,
        db: Session,
        target_type: TargetType,
        list_ids: list[int] | None,
    ) -> Sequence[RBLList]:
        stmt = select(RBLList).where(RBLList.is_enabled.is_(True)).order_by(RBLList.priority.asc())
        lists = db.execute(stmt).scalars().all()
        if list_ids:
            allowed = set(list_ids)
            lists = [rbl for rbl in lists if rbl.id in allowed]

        if target_type == TargetType.IPV4:
            return [r for r in lists if r.supports_ipv4]
        if target_type == TargetType.IPV6:
            return [r for r in lists if r.supports_ipv6]
        if target_type == TargetType.DOMAIN:
            return [r for r in lists if r.supports_domain]
        return [r for r in lists if r.supports_hostname or r.supports_domain]

    async def _run(
        self,
        db: Session,
        monitor_id: int | None,
        user_id: int | None,
        target_type: TargetType,
        target_value: str,
        lists: Sequence[RBLList],
    ) -> CheckRun:
        started = time.perf_counter()

        async def run_one(rbl: RBLList) -> DNSCheckOutcome:
            async with self.semaphore:
                return await self.engine.run_list_check(target_type.value, target_value, rbl)

        outcomes = await asyncio.gather(*(run_one(r) for r in lists))

        listed_count = 0
        error_count = 0
        degraded_count = 0
        for result in outcomes:
            if result.status == CheckStatus.LISTED:
                listed_count += 1
            if result.status in {CheckStatus.ERROR, CheckStatus.TIMEOUT}:
                error_count += 1
            if result.status == CheckStatus.DEGRADED:
                degraded_count += 1

        self._update_list_health(db, lists, outcomes)

        if listed_count > 0:
            overall = MonitorStatus.LISTED
        elif error_count > 0:
            overall = MonitorStatus.DEGRADED
            degraded_count = max(degraded_count, error_count)
        else:
            overall = MonitorStatus.OK

        previous = None
        if monitor_id is not None:
            previous = (
                db.execute(
                    select(CheckRun)
                    .where(CheckRun.monitor_id == monitor_id)
                    .order_by(desc(CheckRun.run_at))
                    .limit(1)
                )
                .scalars()
                .first()
            )

        run = CheckRun(
            monitor_id=monitor_id,
            user_id=user_id,
            target_type=target_type,
            target_value=target_value,
            overall_status=overall,
            listed_count=listed_count,
            error_count=error_count,
            degraded_count=degraded_count,
            duration_ms=int((time.perf_counter() - started) * 1000),
            diff_summary=summarize_diff(previous, listed_count, error_count),
            run_at=utcnow(),
        )
        db.add(run)
        db.flush()

        for rbl, out in zip(lists, outcomes, strict=False):
            db.add(
                CheckRunResult(
                    check_run_id=run.id,
                    list_id=rbl.id,
                    list_name=rbl.name,
                    dns_zone=rbl.dns_zone,
                    status=out.status,
                    answer_code=out.answer_code,
                    txt_record=out.txt_record,
                    category=rbl.list_type.value,
                    severity=rbl.severity,
                    detail_url=rbl.delist_url or rbl.url,
                    raw_error=out.raw_error,
                )
            )

        if monitor_id is not None:
            monitor = db.get(Monitor, monitor_id)
            if monitor:
                monitor.last_status = overall
                monitor.last_run_at = run.run_at
                monitor.next_run_at = run.run_at + self._interval_delta(monitor.interval_minutes)
                monitor.list_ids_csv = to_csv_int(from_csv_int(monitor.list_ids_csv))

        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def _interval_delta(interval_minutes: int):
        from datetime import timedelta

        return timedelta(minutes=interval_minutes)

    def _update_list_health(self, db: Session, lists: Sequence[RBLList], outcomes: Sequence[DNSCheckOutcome]) -> None:
        for rbl, outcome in zip(lists, outcomes, strict=False):
            if outcome.status in {CheckStatus.ERROR, CheckStatus.TIMEOUT}:
                rbl.consecutive_failures += 1
                if outcome.status == CheckStatus.ERROR:
                    rbl.error_count += 1
                else:
                    rbl.timeout_count += 1
                rbl.health_score = max(0, rbl.health_score - 8)
            else:
                rbl.success_count += 1
                rbl.consecutive_failures = 0
                rbl.health_score = min(100, rbl.health_score + 2)

            rbl.is_degraded = rbl.health_score < settings.list_health_degrade_threshold

        db.flush()
