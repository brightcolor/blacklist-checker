import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import router
from app.api.routes import ui
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
_rate = defaultdict(deque)


def _check_rate_limit(ip: str) -> None:
    now = time.time()
    window = 60
    q = _rate[ip]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= settings.public_lookup_rate_per_minute:
        raise HTTPException(status_code=429, detail="rate_limit_exceeded")
    q.append(now)


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="RBL Guard", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def limit_public_checks(request: Request, call_next):
        if request.url.path.endswith("/api/v1/checks/run"):
            client_ip = request.client.host if request.client else "unknown"
            _check_rate_limit(client_ip)
        return await call_next(request)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    app.include_router(router, prefix=settings.api_prefix)
    app.include_router(ui.router)
    app.mount(
        "/static",
        StaticFiles(directory=str(Path(__file__).resolve().parent / "static")),
        name="static",
    )

    return app


app = create_app()
