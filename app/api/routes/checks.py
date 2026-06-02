from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.deps import get_db
from app.models.monitor import CheckRunResult, TargetType
from app.models.user import User
from app.schemas.api import ManualCheckIn, RunOut
from app.services.check_service import CheckService
from app.services.validation import ValidationError, normalize_target

router = APIRouter()
service = CheckService()


@router.post("/run", response_model=RunOut)
async def run_check(
    payload: ManualCheckIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RunOut:
    try:
        target = normalize_target(payload.target_type.value, payload.target_value)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    run = await service.run_manual_check(db, TargetType(payload.target_type), target, payload.list_ids, user.id)
    results = db.execute(select(CheckRunResult).where(CheckRunResult.check_run_id == run.id)).scalars().all()
    fcrdns = None
    if payload.target_type in {TargetType.IPV4, TargetType.IPV6}:
        fcrdns = await service.engine.fcrdns(target)
    return RunOut(
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
        fcrdns=fcrdns,
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
