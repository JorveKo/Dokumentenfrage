# app/core/scraper.py
"""
Core Scraper Modul - Hauptlogik für den intelligenten Dokumenten-Scraper.
Verwaltet den gesamten Scraping-Prozess, Sessions und die Koordination 
zwischen Suche, Download und Verarbeitung.
"""

from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import asyncio
from googleapiclient.discovery import build
import aiohttp
from .session import ScrapingSession  # Neue Import-Zeile
from config import (
    GOOGLE_API_KEY, 
    GOOGLE_CSE_ID, 
    MAX_PARALLEL_DOWNLOADS,
    API_COST_PER_REQUEST, 
    BATCH_SIZE
)
from models import ScrapingStatus, ScrapingStats, DocumentMetadata
from app.utils.text.text_processor import text_processor
from app.utils.term.term_expander import term_expander
from app.utils.rate_limit.rate_limiter import rate_limiter  # Diese Klasse müssen wir noch erstellen
from app.database.manager import db_manager
from .downloader import document_downloader
from .processor import document_processor


logger = logging.getLogger(__name__)




MAX_DAILY_REQUESTS = 500
CURRENT_REQUESTS = 0

async def check_api_limits():
    global CURRENT_REQUESTS
    if CURRENT_REQUESTS >= MAX_DAILY_REQUESTS:
        raise Exception("Tägliches API-Limit erreicht")
    CURRENT_REQUESTS += 1


    
    def __post_init__(self):
        self.processed_urls = set()

class ScraperEngine:
    """Hauptklasse für den intelligenten Scraping-Prozess"""
    
    def __init__(self):
        self.google_client = build('customsearch', 'v1', developerKey=GOOGLE_API_KEY)
        self.status = ScrapingStatus()
        self.stats = ScrapingStats()
        self.active_sessions: Dict[str, ScrapingSession] = {}
        self.session: Optional[aiohttp.ClientSession] = None

 

    async def init_session(self):
        """Initialisiert die HTTP Session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def close_session(self):
        """Schließt die HTTP Session"""
        if self.session:
            await self.session.close()
            self.session = None
            
    async def start_scraping(
        self,
        term: str,
        file_type: str,
        max_results: int,
        similarity_threshold: float
    ) -> str:
        """Startet einen neuen Scraping-Prozess"""
        session_id = f"{term}_{datetime.now().timestamp()}"
        
        # Erstelle neue Session
        session = ScrapingSession(
            term=term,
            file_type=file_type,
            max_results=max_results,
            similarity_threshold=similarity_threshold,
            start_time=datetime.now()
        )
        self.active_sessions[session_id] = session
        
        # Starte Scraping im Hintergrund
        asyncio.create_task(self._run_scraping(session_id))
        
        return session_id
        
    async def _run_scraping(self, session_id: str):
        """Führt den Scraping-Prozess aus"""
        session = self.active_sessions[session_id]
        self.status.is_running = True
        self.status.current_term = session.term
        
        try:
            await self.init_session()
            
            # Erweitere Suchbegriffe
            expanded_terms = term_expander.expand_term(session.term)
            logger.info(f"Erweiterte Begriffe: {expanded_terms}")
            self.status.total_documents = len(expanded_terms) * session.max_results
            
            # Verarbeite jeden Begriff
            for term in expanded_terms:
                if not self.status.is_running:
                    break
                    
                await self._process_term(session, term)
                self.status.completed_terms.add(term)
                
            logger.info(f"Scraping abgeschlossen für Session {session_id}")
            
        except Exception as e:
            logger.error(f"Fehler im Scraping-Prozess: {str(e)}")
            self.status.error = str(e)
        finally:
            await self.close_session()
            self.status.is_running = False
            await self._cleanup_session(session_id)
            
    async def _process_term(self, session: ScrapingSession, term: str):
        """Verarbeitet einen einzelnen Suchbegriff"""
        try:
            # Suche Dokumente
            search_results = await self._search_documents(term, session.file_type, 
                                                        session.max_results)
            # Debug-Log
            logger.debug(f"Typ von session.processed_urls: {type(session.processed_urls)}")
            logger.debug(f"Typ von search_results: {type(search_results)}")
            
            if not search_results:
                logger.warning(f"Keine Ergebnisse gefunden für Term: {term}")
                return
                
            # Erstelle Download-Tasks
            tasks = []
            for result in search_results:
                # Debug-Log
                logger.debug(f"Verarbeite URL: {result.get('link')}")
                logger.debug(f"processed_urls vor add: {session.processed_urls}")
                

                    
                if result['link'] not in session.processed_urls:
                    session.processed_urls.add(result['link'])
                    tasks.append(self._process_search_result(
                        session, result, term
                    ))
                    
            # Verarbeite Downloads in Batches
            for i in range(0, len(tasks), MAX_PARALLEL_DOWNLOADS):
                batch = tasks[i:i + MAX_PARALLEL_DOWNLOADS]
                completed = await asyncio.gather(*batch, return_exceptions=True)
                
                # Verarbeite Ergebnisse
                for result in completed:
                    if isinstance(result, Exception):
                        logger.error(f"Fehler bei der Verarbeitung: {str(result)}")
                        session.failed_downloads += 1
                    elif result:
                        session.successful_downloads += 1
                        session.total_bytes += result.get('size', 0)
                        
            # Update Fortschritt
            total_processed = len(session.processed_urls)
            total_expected = self.status.total_documents
            self.status.progress = (total_processed / total_expected * 100) if total_expected > 0 else 0
            
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung von Term '{term}': {str(e)}")
        
    async def _search_documents(self, term: str, file_type: str, max_results: int) -> List[Dict]:
        """Führt die Google-Suche durch"""
        try:
            # Debug-Logs hinzufügen
            logger.info(f"Search request with key: {GOOGLE_API_KEY}")
            logger.info(f"Search request with CSE ID: {GOOGLE_CSE_ID}")
            
            await check_api_limits()
            file_type_str = f"filetype:{file_type}"
            results = []
            
            for i in range(0, min(max_results, 100), BATCH_SIZE):
                response = self.google_client.cse().list(
                    q=f"{term} {file_type_str}",
                    cx=GOOGLE_CSE_ID,
                    start=i + 1,
                    num=min(BATCH_SIZE, max_results - i)
                ).execute()
                
                if 'items' in response:
                    results.extend(response['items'])
                    self.status.api_costs += API_COST_PER_REQUEST
                    
            return results
            
        except Exception as e:
            logger.error(f"Fehler bei der Google-Suche: {str(e)}")
            return []
            
    async def _process_search_result(
        self,
        session: ScrapingSession,
        result: Dict,
        term: str
    ) -> Optional[DocumentMetadata]:
        """Verarbeitet ein einzelnes Suchergebnis"""
        try:
            # Download Dokument
            doc_info = await document_downloader.download(
                result['link'],
                session.file_type
            )
            
            if not doc_info:
                return None
                
            # Verarbeite Dokument
            processed_doc = await document_processor.process(
                doc_info,
                term=term,
                similarity_threshold=session.similarity_threshold,
                snippet=result.get('snippet', '')
            )
            
            if processed_doc:
                # Speichere in Datenbank
                if await db_manager.store_document(processed_doc):
                    return processed_doc
                    
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei der Verarbeitung des Suchergebnisses: {str(e)}")
            return None
            
    async def _cleanup_session(self, session_id: str):
        """Räumt eine beendete Session auf"""
        try:
            session = self.active_sessions.pop(session_id)
            duration = (datetime.now() - session.start_time).total_seconds()
            
            # Aktualisiere Statistiken
            self.stats.total_documents += session.successful_downloads
            self.stats.total_size += session.total_bytes
            
            if session.successful_downloads > 0:
                self.stats.success_rate = (
                    session.successful_downloads /
                    (session.successful_downloads + session.failed_downloads)
                ) * 100
                
            self.stats.processing_speed = \
                session.successful_downloads / (duration / 60) if duration > 0 else 0
                
            # Log Session-Zusammenfassung
            logger.info(f"""
            Session {session_id} abgeschlossen:
            - Erfolgreiche Downloads: {session.successful_downloads}
            - Fehlgeschlagene Downloads: {session.failed_downloads}
            - Gesamtgröße: {session.total_bytes / 1024 / 1024:.2f} MB
            - Dauer: {duration:.2f} Sekunden
            """)
            
        except Exception as e:
            logger.error(f"Fehler beim Cleanup der Session: {str(e)}")
            
    def get_session_status(self, session_id: str) -> Dict:
        """Gibt den Status einer Session zurück"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {}
            
        return {
            'term': session.term,
            'file_type': session.file_type,
            'successful_downloads': session.successful_downloads,
            'failed_downloads': session.failed_downloads,
            'total_bytes': session.total_bytes,
            'duration': (datetime.now() - session.start_time).total_seconds(),
            'processed_urls': len(session.processed_urls)
        }
        
    def stop_scraping(self):
        """Stoppt alle laufenden Scraping-Prozesse"""
        self.status.is_running = False
        logger.info("Scraping-Prozess wird gestoppt")

# Globale Scraper-Instanz
scraper_engine = ScraperEngine()