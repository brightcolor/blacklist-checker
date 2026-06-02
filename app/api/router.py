from fastapi import APIRouter

from app.api.routes import auth, channels, checks, dashboard, lists, monitors, system

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(checks.router, prefix="/checks", tags=["checks"])
router.include_router(monitors.router, prefix="/monitors", tags=["monitors"])
router.include_router(lists.router, prefix="/lists", tags=["lists"])
router.include_router(channels.router, prefix="/channels", tags=["channels"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
router.include_router(system.router, prefix="/system", tags=["system"])
