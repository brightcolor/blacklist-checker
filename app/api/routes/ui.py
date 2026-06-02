from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def ui_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
