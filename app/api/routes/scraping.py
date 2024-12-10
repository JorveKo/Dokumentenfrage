from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging
from models import (
    ScrapingRequest,
    ScrapingStatus,
    ScrapingStats
)
from app.core.scraper import scraper_engine
from app.database.manager import db_manager
from app.utils.term.term_expander import term_expander

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/scraping/start")
async def start_scraping(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Startet einen neuen Scraping-Prozess"""
    try:
        if scraper_engine.status.is_running:
            raise HTTPException(
                status_code=400,
                detail="Ein Scraping-Prozess läuft bereits"
            )
        
        session_id = await scraper_engine.start_scraping(
            term=request.term,
            file_type=request.file_type,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold
        )
        
        return {
            "status": "success",
            "message": "Scraping-Prozess gestartet",
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Fehler beim Starten des Scraping-Prozesses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Starten: {str(e)}")

@router.post("/api/scraping/stop")
async def stop_scraping() -> dict:
    """Stoppt den laufenden Scraping-Prozess"""
    try:
        scraper_engine.stop_scraping()
        return {
            "status": "success",
            "message": "Scraping-Prozess wird gestoppt"
        }
    except Exception as e:
        logger.error(f"Fehler beim Stoppen des Scraping-Prozesses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Stoppen: {str(e)}")

@router.get("/api/scraping/status")
async def get_status() -> ScrapingStatus:
    """Gibt den aktuellen Status des Scraping-Prozesses zurück"""
    try:
        return scraper_engine.status
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Status: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen des Status")

@router.get("/api/scraping/stats")
async def get_stats() -> ScrapingStats:
    """Gibt Statistiken über alle gescrapten Dokumente zurück"""
    try:
        return await db_manager.get_statistics()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Statistiken: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen der Statistiken")

@router.get("/api/scraping/session/{session_id}")
async def get_session_status(session_id: str) -> dict:
    """
    Gibt den Status einer spezifischen Scraping-Session zurück
    
    Args:
        session_id: ID der Session
        
    Returns:
        dict: Session-Status und Statistiken
    """
    try:
        status = scraper_engine.get_session_status(session_id)
        if not status:
            raise HTTPException(status_code=404, detail=f"Session {session_id} nicht gefunden")
        return status
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Session-Status: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Abrufen des Session-Status")