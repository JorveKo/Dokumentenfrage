"""
Status Manager für den Scraping-Prozess.
Verwaltet und überwacht den Status aller Scraping-Operationen.
"""

from datetime import datetime
from typing import Dict, Optional, List, Set
import logging
from dataclasses import dataclass, asdict
from models import ScrapingStatus
from app.database.manager import db_manager

logger = logging.getLogger(__name__)

@dataclass
class SessionStatus:
    """Status einer einzelnen Scraping-Session"""
    session_id: str
    term: str
    file_type: str
    max_results: int
    similarity_threshold: float
    start_time: datetime
    end_time: Optional[datetime] = None
    documents_found: int = 0
    documents_downloaded: int = 0
    documents_failed: int = 0
    current_url: Optional[str] = None
    processed_urls: Set[str] = None
    total_bytes: int = 0
    status: str = "running"
    error: Optional[str] = None
    completed_terms: Set[str] = None

    def __post_init__(self):
        """Initialisiert die Sets nach der Objekterstellung"""
        if self.processed_urls is None:
            self.processed_urls = set()
        if self.completed_terms is None:
            self.completed_terms = set()

class StatusManager:
    """
    Verwaltet den Status des Scraping-Prozesses und einzelner Sessions.
    
    Attributes:
        is_running (bool): Gibt an, ob aktuell ein Scraping-Prozess läuft
        current_session (Optional[str]): ID der aktuellen Session
        sessions (Dict): Speichert alle Session-Status-Objekte
    """
    
    def __init__(self):
        self.is_running: bool = False
        self.current_session: Optional[str] = None
        self.sessions: Dict[str, SessionStatus] = {}
        self.api_costs: float = 0.0
        
    def start_session(
        self,
        session_id: str,
        term: str,
        file_type: str,
        max_results: int,
        similarity_threshold: float
    ) -> SessionStatus:
        """
        Startet eine neue Scraping-Session
        
        Args:
            session_id: Eindeutige ID für die Session
            term: Suchbegriff
            file_type: Dateityp
            max_results: Maximale Ergebnisse
            similarity_threshold: Ähnlichkeits-Schwellenwert
            
        Returns:
            SessionStatus: Status-Objekt der neuen Session
        """
        if self.is_running:
            raise RuntimeError("Es läuft bereits eine Scraping-Session")
            
        session = SessionStatus(
            session_id=session_id,
            term=term,
            file_type=file_type,
            max_results=max_results,
            similarity_threshold=similarity_threshold,
            start_time=datetime.now()
        )
        self.sessions[session_id] = session
        self.current_session = session_id
        self.is_running = True
        
        logger.info(f"Neue Scraping-Session gestartet: {session_id}")
        return session
    
    def end_session(self, session_id: str, error: Optional[str] = None):
        """
        Beendet eine Scraping-Session
        
        Args:
            session_id: ID der zu beendenden Session
            error: Optional, Fehlermeldung falls die Session mit Fehler endet
        """
        if session_id not in self.sessions:
            raise ValueError(f"Unbekannte Session-ID: {session_id}")
            
        session = self.sessions[session_id]
        session.end_time = datetime.now()
        session.status = "error" if error else "completed"
        session.error = error
        
        if self.current_session == session_id:
            self.current_session = None
            self.is_running = False
            
        logger.info(f"Scraping-Session beendet: {session_id}")
    
    def update_session(
        self,
        session_id: str,
        documents_found: Optional[int] = None,
        documents_downloaded: Optional[int] = None,
        documents_failed: Optional[int] = None,
        current_url: Optional[str] = None
    ):
        """
        Aktualisiert den Status einer Session
        
        Args:
            session_id: ID der zu aktualisierenden Session
            documents_found: Anzahl gefundener Dokumente
            documents_downloaded: Anzahl heruntergeladener Dokumente
            documents_failed: Anzahl fehlgeschlagener Downloads
            current_url: Aktuelle URL die gescrapt wird
        """
        if session_id not in self.sessions:
            raise ValueError(f"Unbekannte Session-ID: {session_id}")
            
        session = self.sessions[session_id]
        
        if documents_found is not None:
            session.documents_found = documents_found
        if documents_downloaded is not None:
            session.documents_downloaded = documents_downloaded
        if documents_failed is not None:
            session.documents_failed = documents_failed
        if current_url is not None:
            session.current_url = current_url
            
    def get_session_status(self, session_id: str) -> Dict:
        """
        Gibt den Status einer Session zurück
        
        Args:
            session_id: ID der Session
            
        Returns:
            Dict: Status-Informationen der Session
        """
        if session_id not in self.sessions:
            raise ValueError(f"Unbekannte Session-ID: {session_id}")
            
        return asdict(self.sessions[session_id])
    
    def get_active_sessions(self) -> List[str]:
        """
        Gibt alle aktiven Session-IDs zurück
        
        Returns:
            List[str]: Liste der aktiven Session-IDs
        """
        return [
            session_id 
            for session_id, session in self.sessions.items() 
            if session.status == "running"
        ]
    
    def get_current_status(self) -> ScrapingStatus:
        """
        Gibt den aktuellen Gesamtstatus zurück
        
        Returns:
            ScrapingStatus: Aktueller Status des Scraping-Systems
        """
        if not self.current_session:
            return ScrapingStatus(is_running=False)
            
        session = self.sessions[self.current_session]
        return ScrapingStatus(
            is_running=self.is_running,
            current_session=self.current_session,
            current_term=session.term,
            documents_found=session.documents_found,
            documents_downloaded=session.documents_downloaded,
            documents_failed=session.documents_failed,
            current_url=session.current_url,
            api_costs=self.api_costs,
            completed_terms=list(session.completed_terms)
        )

    def update_api_costs(self, cost: float):
        """Aktualisiert die API-Kosten"""
        self.api_costs += cost