from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import logging
from app.database.manager import db_manager
from models import Document

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/api/documents/search")
async def search_documents(
    query: str,
    page: int = 1,
    per_page: int = 10
) -> Dict[str, Any]:
    """Durchsucht die gespeicherten Dokumente"""
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
        raise HTTPException(status_code=500, detail="Fehler bei der Dokumentensuche")


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
            raise HTTPException(status_code=404, detail=f"Dokument {document_id} nicht gefunden")
        return {
            "status": "success",
            "message": f"Dokument {document_id} erfolgreich gelöscht"
        }
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Dokuments: {str(e)}")
        raise HTTPException(status_code=500, detail="Fehler beim Löschen des Dokuments")

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