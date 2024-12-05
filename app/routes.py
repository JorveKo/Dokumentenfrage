# app/routes.py
"""
API Routes für den Document Scraper.
Definiert alle HTTP-Endpunkte für die Webanwendung.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import TEMPLATES_DIR, LOGO_FILE
from models import ScrapingRequest, ScrapingStatus, ScrapingStats
from app.core.scraper import scraper_engine
from app.database import db_manager

# Router Setup
router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
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

@router.post("/api/scraping/start")
async def start_scraping(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks
) -> dict:
    """
    Startet einen neuen Scraping-Prozess
    
    Args:
        request: ScrapingRequest mit den Parametern
        background_tasks: Für asynchrone Verarbeitung
        
    Returns:
        dict: Session-ID und Status
    """
    try:
        # Prüfe ob bereits ein Scraping-Prozess läuft
        if scraper_engine.status.is_running:
            raise HTTPException(
                status_code=400,
                detail="Ein Scraping-Prozess läuft bereits"
            )
            
        # Starte Scraping
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
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Starten: {str(e)}"
        )

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
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Stoppen: {str(e)}"
        )

@router.get("/")
async def root():
    return {"message": "Neural Document Acquisition System is running"}

@router.get("/api/scraping/status")
async def get_status() -> ScrapingStatus:
    """Gibt den aktuellen Status des Scraping-Prozesses zurück"""
    try:
        return scraper_engine.status
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Abrufen des Status"
        )

@router.get("/api/scraping/stats")
async def get_stats() -> ScrapingStats:
    """Gibt Statistiken über alle gescrapten Dokumente zurück"""
    try:
        return await db_manager.get_statistics()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Statistiken: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Abrufen der Statistiken"
        )

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
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} nicht gefunden"
            )
        return status
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Session-Status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Abrufen des Session-Status"
        )

@router.get("/api/documents/search")
async def search_documents(
    query: str,
    page: int = 1,
    per_page: int = 10
) -> dict:
    """
    Durchsucht die gespeicherten Dokumente
    
    Args:
        query: Suchbegriff
        page: Seitennummer für Pagination
        per_page: Anzahl der Ergebnisse pro Seite
        
    Returns:
        dict: Suchergebnisse und Metadata
    """
    try:
        skip = (page - 1) * per_page
        results = await db_manager.search_documents(
            query,
            skip=skip,
            limit=per_page
        )
        
        total = await db_manager.count_search_results(query)
        
        return {
            "results": results,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }
    except Exception as e:
        logger.error(f"Fehler bei der Dokumentensuche: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Fehler bei der Dokumentensuche"
        )

@router.delete("/api/documents/{document_id}")
async def delete_document(document_id: str) -> dict:
    """
    Löscht ein Dokument aus der Datenbank
    
    Args:
        document_id: ID des zu löschenden Dokuments
        
    Returns:
        dict: Status der Löschoperation
    """
    try:
        success = await db_manager.delete_document(document_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Dokument {document_id} nicht gefunden"
            )
        return {
            "status": "success",
            "message": f"Dokument {document_id} erfolgreich gelöscht"
        }
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Dokuments: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Löschen des Dokuments"
        )

@router.get("/api/health")
async def health_check():
    """Überprüft den Gesundheitszustand des Systems"""
    try:
        # Prüfe Datenbankverbindung
        db_connected = await db_manager.connect()
        
        # Prüfe Dateisystem
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

@router.get("/api/documents/recent")
async def get_recent_documents(limit: int = 10):
    """Holt die neuesten Dokumente"""
    try:
        documents = await db_manager.get_recent_documents(limit=limit)
        return {
            "documents": documents,
            "total_count": await db_manager.get_document_count()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))