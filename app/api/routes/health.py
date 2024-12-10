from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging
from app.core.scraper import scraper_engine
from app.database.manager import db_manager
from config import TEMPLATES_DIR

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Überprüft den Gesundheitszustand des Systems"""
    try:
        db_connected = await db_manager.connect()
        downloads_ok = TEMPLATES_DIR.exists() and TEMPLATES_DIR.is_dir()
        
        return {
            "status": "healthy" if db_connected and downloads_ok else "unhealthy",
            "database": "connected" if db_connected else "disconnected",
            "filesystem": "ok" if downloads_ok else "error",
            "scraping_active": scraper_engine.status.is_running
        }
    except Exception as e:
        logger.error(f"Fehler beim Health Check: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }