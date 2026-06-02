from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready", "time": datetime.now(tz=timezone.utc).isoformat()}
