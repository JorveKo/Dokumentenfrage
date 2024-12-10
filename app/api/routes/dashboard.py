from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any
import logging
from app.config import TEMPLATES_DIR, LOGO_FILE

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request) -> HTMLResponse:
    """Rendert das Dashboard"""
    try:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "logo_exists": LOGO_FILE.exists(),
                "title": "Neural Document Acquisition System"
            }
        )
    except Exception as e:
        logger.error(f"Fehler beim Rendern des Dashboards: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")