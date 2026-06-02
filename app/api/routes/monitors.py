from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.deps import get_db
from app.models.monitor import CheckRun, CheckRunResult, Monitor
from app.models.user import User
from app.schemas.api import MonitorIn, MonitorOut, RunOut
from app.services.csv_utils import from_csv_int, to_csv_int
from app.services.validation import ValidationError, normalize_target

router = APIRouter()


@router.get("", response_model=list[MonitorOut])
def list_monitors(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[MonitorOut]:
    monitors = db.execute(select(Monitor).where(Monitor.user_id == user.id).order_by(Monitor.created_at.desc())).scalars().all()
    return [
        MonitorOut(
            id=m.id,
            name=m.name,
            target_type=m.target_type,
            target_value=m.target_value,
            interval_minutes=m.interval_minutes,
            list_ids=from_csv_int(m.list_ids_csv),
            sensitivity=m.sensitivity,
            maintenance_mode=m.maintenance_mode,
            is_enabled=m.is_enabled,
            last_status=m.last_status,
            last_run_at=m.last_run_at,
            next_run_at=m.next_run_at,
        )
        for m in monitors
    ]


@router.post("", response_model=MonitorOut)
def create_monitor(
    payload: MonitorIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MonitorOut:
    try:
        target = normalize_target(payload.target_type.value, payload.target_value)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    monitor = Monitor(
        user_id=user.id,
        name=payload.name,
        target_type=payload.target_type,
        target_value=target,
        interval_minutes=payload.interval_minutes,
        list_ids_csv=to_csv_int(payload.list_ids),
        sensitivity=payload.sensitivity,
        maintenance_mode=payload.maintenance_mode,
        is_enabled=payload.is_enabled,
        next_run_at=None,
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return MonitorOut(
        id=monitor.id,
        name=monitor.name,
        target_type=monitor.target_type,
        target_value=monitor.target_value,
        interval_minutes=monitor.interval_minutes,
        list_ids=from_csv_int(monitor.list_ids_csv),
        sensitivity=monitor.sensitivity,
        maintenance_mode=monitor.maintenance_mode,
        is_enabled=monitor.is_enabled,
        last_status=monitor.last_status,
        last_run_at=monitor.last_run_at,
        next_run_at=monitor.next_run_at,
    )


@router.get("/{monitor_id}", response_model=MonitorOut)
def get_monitor(
    monitor_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MonitorOut:
    monitor = db.get(Monitor, monitor_id)
    if not monitor or monitor.user_id != user.id:
        raise HTTPException(status_code=404, detail="not_found")
    return MonitorOut(
        id=monitor.id,
        name=monitor.name,
        target_type=monitor.target_type,
        target_value=monitor.target_value,
        interval_minutes=monitor.interval_minutes,
        list_ids=from_csv_int(monitor.list_ids_csv),
        sensitivity=monitor.sensitivity,
        maintenance_mode=monitor.maintenance_mode,
        is_enabled=monitor.is_enabled,
        last_status=monitor.last_status,
        last_run_at=monitor.last_run_at,
        next_run_at=monitor.next_run_at,
    )


@router.put("/{monitor_id}", response_model=MonitorOut)
def update_monitor(
    monitor_id: int,
    payload: MonitorIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MonitorOut:
    monitor = db.get(Monitor, monitor_id)
    if not monitor or monitor.user_id != user.id:
        raise HTTPException(status_code=404, detail="not_found")
    target = normalize_target(payload.target_type.value, payload.target_value)
    monitor.name = payload.name
    monitor.target_type = payload.target_type
    monitor.target_value = target
    monitor.interval_minutes = payload.interval_minutes
    monitor.list_ids_csv = to_csv_int(payload.list_ids)
    monitor.sensitivity = payload.sensitivity
    monitor.maintenance_mode = payload.maintenance_mode
    monitor.is_enabled = payload.is_enabled
    if monitor.last_run_at:
        monitor.next_run_at = monitor.last_run_at + timedelta(minutes=monitor.interval_minutes)
    db.commit()
    db.refresh(monitor)
    return MonitorOut(
        id=monitor.id,
        name=monitor.name,
        target_type=monitor.target_type,
        target_value=monitor.target_value,
        interval_minutes=monitor.interval_minutes,
        list_ids=from_csv_int(monitor.list_ids_csv),
        sensitivity=monitor.sensitivity,
        maintenance_mode=monitor.maintenance_mode,
        is_enabled=monitor.is_enabled,
        last_status=monitor.last_status,
        last_run_at=monitor.last_run_at,
        next_run_at=monitor.next_run_at,
    )


@router.delete("/{monitor_id}")
def delete_monitor(
    monitor_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, bool]:
    monitor = db.get(Monitor, monitor_id)
    if not monitor or monitor.user_id != user.id:
        raise HTTPException(status_code=404, detail="not_found")
    db.delete(monitor)
    db.commit()
    return {"ok": True}


@router.get("/{monitor_id}/runs", response_model=list[RunOut])
def monitor_runs(
    monitor_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[RunOut]:
    monitor = db.get(Monitor, monitor_id)
    if not monitor or monitor.user_id != user.id:
        raise HTTPException(status_code=404, detail="not_found")

    runs = (
        db.execute(select(CheckRun).where(CheckRun.monitor_id == monitor.id).order_by(CheckRun.run_at.desc()).limit(200))
        .scalars()
        .all()
    )
    output: list[RunOut] = []
    for run in runs:
        results = db.execute(select(CheckRunResult).where(CheckRunResult.check_run_id == run.id)).scalars().all()
        output.append(
            RunOut(
                id=run.id,
                monitor_id=run.monitor_id,
                target_type=run.target_type,
                target_value=run.target_value,
                overall_status=run.overall_status,
                listed_count=run.listed_count,
                error_count=run.error_count,
                degraded_count=run.degraded_count,
                duration_ms=run.duration_ms,
                diff_summary=run.diff_summary,
                run_at=run.run_at,
                results=[
                    {
                        "list_id": item.list_id,
                        "list_name": item.list_name,
                        "dns_zone": item.dns_zone,
                        "status": item.status,
                        "answer_code": item.answer_code,
                        "txt_record": item.txt_record,
                        "category": item.category,
                        "severity": item.severity,
                        "detail_url": item.detail_url,
                        "raw_error": item.raw_error,
                    }
                    for item in results
                ],
            )
        )
    return output
