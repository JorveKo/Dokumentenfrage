# app.py
import os
import logging
import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set

import nltk
from nltk.corpus import wordnet
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pymongo import MongoClient
from googleapiclient.discovery import build
import requests
import torch
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

# Download required NLTK dat
nltk.download('wordnet', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

# Konstanten für die Google API
from secure_api_credentials import GOOGLE_API_KEY, GOOGLE_CSE_ID
from googleapiclient.discovery import build

drive_service = build('drive', 'v3', developerKey=GOOGLE_API_KEY)


# Rest of your web scraper code

DOWNLOAD_FOLDER = "Downloads"
MONGODB_URI = "mongodb://localhost:27017/"
DB_NAME = "document_scraper"
MAX_PARALLEL_DOWNLOADS = 5

# FastAPI App
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log')
    ]
)
logger = logging.getLogger(__name__)

# Stelle sicher, dass der Download-Ordner existiert
Path(DOWNLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

class ScraperStatus:
    """Status-Tracking für den Scraper"""
    def __init__(self):
        self.current_progress = 0
        self.total_documents = 0
        self.current_term = ""
        self.completed_terms = set()
        self.api_costs = 0.0
        self.is_running = False
        self.error = None
        self.downloaded_files = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.total_bytes = 0

status = ScraperStatus()

class DocumentScraper:
    """Hauptklasse für das Dokument-Scraping"""
    def __init__(self):
        # Initialisiere MongoDB
        try:
            self.client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
            self.client.server_info()
            self.db = self.client[DB_NAME]
            logger.info("MongoDB Verbindung erfolgreich hergestellt")
        except Exception as e:
            logger.error(f"MongoDB Verbindungsfehler: {str(e)}")
            # Fallback zu einer einfachen Liste
            self.mock_db = []
            logger.info("Verwende temporären Speicher")

        self.search_service = build('customsearch', 'v1', developerKey=GOOGLE_API_KEY)
        self.vectorizer = TfidfVectorizer()
        self.domain_terms = self.load_domain_terms()

    def load_domain_terms(self) -> Set[str]:
        """Lädt domänenspezifische Begriffe"""
        return {
            "vertrag", "analyse", "dokument", "bericht", "handbuch",
            "anleitung", "spezifikation", "documentation", "manual",
            "guide", "report", "specification"
        }

    def get_related_terms(self, term: str) -> List[str]:
        """Findet verwandte Begriffe"""
        related_terms = set([term])
        try:
            # WordNet-Synonyme
            for syn in wordnet.synsets(term, lang='deu'):
                related_terms.update(lemma.name() for lemma in syn.lemmas())
                
                # Verwandte Begriffe
                for hypernym in syn.hypernyms():
                    related_terms.update(lemma.name() for lemma in hypernym.lemmas())
                for hyponym in syn.hyponyms():
                    related_terms.update(lemma.name() for lemma in hyponym.lemmas())

            # Domänenspezifische Erweiterungen
            for domain_term in self.domain_terms:
                if domain_term in term.lower():
                    related_terms.add(f"{term}_{domain_term}")

        except Exception as e:
            logger.error(f"Fehler bei der Begriffserweiterung: {str(e)}")

        return list(related_terms)

    def calculate_similarity(self, doc1: str, doc2: str) -> float:
        """Berechnet die Ähnlichkeit zwischen zwei Dokumenten"""
        try:
            tfidf_matrix = self.vectorizer.fit_transform([doc1, doc2])
            return float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
        except Exception as e:
            logger.error(f"Fehler bei der Ähnlichkeitsberechnung: {str(e)}")
            return 0.0

    def search_documents(self, term: str, file_type: str, max_results: int) -> List[Dict]:
        """Sucht Dokumente über die Google API"""
        try:
            file_type_str = f"filetype:{file_type}"
            results = []
            
            for i in range(0, min(max_results, 100), 10):
                response = self.search_service.cse().list(
                    q=f"{term} {file_type_str}",
                    cx=GOOGLE_CSE_ID,
                    start=i + 1,
                    num=min(10, max_results - i)
                ).execute()
                
                if 'items' in response:
                    results.extend(response['items'])
                    status.api_costs += 0.005  # Kosten pro API-Aufruf

            return results
        except Exception as e:
            logger.error(f"Fehler bei der Google-Suche: {str(e)}")
            return []

    def download_document(self, url: str, file_type: str) -> Optional[Dict]:
        """Lädt ein Dokument herunter und speichert es"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{hashlib.md5(url.encode()).hexdigest()[:8]}"
            
            content_type = response.headers.get('content-type', '')
            if file_type.lower() in content_type.lower():
                file_extension = file_type.lower()
                full_path = os.path.join(DOWNLOAD_FOLDER, f"{filename}.{file_extension}")
                
                with open(full_path, 'wb') as f:
                    f.write(response.content)
                
                status.downloaded_files += 1
                status.successful_downloads += 1
                status.total_bytes += len(response.content)
                
                return {
                    'url': url,
                    'local_path': full_path,
                    'content_type': content_type,
                    'size': len(response.content),
                    'timestamp': timestamp
                }
            
            return None
        except Exception as e:
            status.failed_downloads += 1
            logger.error(f"Fehler beim Download von {url}: {str(e)}")
            return None

def start_scraping(term: str, file_type: str, max_results: int, similarity_threshold: float):
    """Startet den Scraping-Prozess in einem separaten Thread"""
    def scraping_task():
        try:
            status.is_running = True
            status.current_term = term
            status.total_documents = max_results
            status.current_progress = 0
            status.error = None
            
            scraper = DocumentScraper()
            
            # Erweiterte Begriffe finden
            related_terms = scraper.get_related_terms(term)
            total_terms = len(related_terms)
            
            for i, current_term in enumerate(related_terms):
                if not status.is_running:
                    break
                
                logger.info(f"Verarbeite Begriff: {current_term}")
                
                # Suche Dokumente
                search_results = scraper.search_documents(current_term, file_type, 
                                                        max_results // total_terms)
                
                for j, result in enumerate(search_results):
                    if not status.is_running:
                        break
                        
                    # Download und Verarbeitung
                    doc_info = scraper.download_document(result['link'], file_type)
                    
                    if doc_info:
                        # Prüfe Ähnlichkeit
                        existing_docs = scraper.db.documents.find({'term': current_term})
                        is_duplicate = False
                        
                        for existing_doc in existing_docs:
                            similarity = scraper.calculate_similarity(
                                result.get('snippet', ''),
                                existing_doc.get('snippet', '')
                            )
                            if similarity > similarity_threshold:
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            # Speichere in MongoDB
                            doc_data = {
                                'term': current_term,
                                'url': result['link'],
                                'title': result.get('title', ''),
                                'snippet': result.get('snippet', ''),
                                'file_type': file_type,
                                'local_path': doc_info['local_path'],
                                'content_type': doc_info['content_type'],
                                'size': doc_info['size'],
                                'timestamp': doc_info['timestamp'],
                                'hash': hashlib.md5(result.get('snippet', '').encode()).hexdigest()
                            }
                            
                            try:
                                scraper.db.documents.insert_one(doc_data)
                            except Exception as e:
                                logger.error(f"Fehler beim Speichern in MongoDB: {str(e)}")
                                # Fallback zu temporärem Speicher
                                scraper.mock_db.append(doc_data)
                    
                    # Update Fortschritt
                    total_progress = (i * len(search_results) + j + 1) / \
                                   (total_terms * len(search_results))
                    status.current_progress = total_progress * 100
                
                status.completed_terms.add(current_term)
            
            status.is_running = False
            logger.info(f"Scraping für Term '{term}' abgeschlossen")
            
        except Exception as e:
            error_msg = f"Fehler beim Scraping: {str(e)}"
            logger.error(error_msg)
            status.error = error_msg
            status.is_running = False

    # Starte den Prozess in einem separaten Thread
    import threading
    thread = threading.Thread(target=scraping_task)
    thread.start()

@app.get("/", response_class=HTMLResponse)
async def get_index(request):
    """Rendert das Dashboard"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/start")
async def api_start_scraping(data: dict):
    """API-Endpunkt zum Starten des Scrapings"""
    try:
        logger.info(f"Empfangene Daten: {data}")
        
        term = data.get('term')
        file_type = data.get('file_type')
        max_results = int(data.get('max_results', 10))
        similarity_threshold = float(data.get('similarity_threshold', 0.85))
        
        if not all([term, file_type]):
            return {'error': 'Fehlende Parameter'}
            
        logger.info(f"Starte Scraping für: Term={term}, Type={file_type}, Max={max_results}")
        
        if status.is_running:
            return {'error': 'Scraper läuft bereits'}
            
        start_scraping(term, file_type, max_results, similarity_threshold)
        return {'message': 'Scraping gestartet'}
        
    except Exception as e:
        logger.error(f"Fehler beim Starten des Scrapers: {str(e)}")
        return {'error': f'Fehler: {str(e)}'}

@app.post("/api/stop")
async def stop_scraping():
    """Stoppt den Scraping-Prozess"""
    status.is_running = False
    return {'message': 'Scraping gestoppt'}

@app.get("/api/status")
async def get_status():
    """Gibt den aktuellen Status zurück"""
    return {
        'progress': status.current_progress,
        'current_term': status.current_term,
        'completed_terms': list(status.completed_terms),
        'is_running': status.is_running,
        'error': status.error,
        'api_costs': status.api_costs,
        'downloaded_files': status.downloaded_files,
        'successful_downloads': status.successful_downloads,
        'failed_downloads': status.failed_downloads,
        'total_bytes': status.total_bytes,
        'total_documents': status.total_documents
    }

@app.get("/api/stats")
async def get_stats():
    """Gibt Statistiken zurück"""
    try:
        scraper = DocumentScraper()
        stats = {
            'total_documents': scraper.db.documents.count_documents({}),
            'documents_per_type': {},
            'documents_per_term': {},
            'total_size': 0
        }
        
        for doc in scraper.db.documents.find():
            file_type = doc.get('file_type', 'unknown')
            term = doc.get('term', 'unknown')
            size = doc.get('size', 0)
            
            stats['documents_per_type'][file_type] = \
                stats['documents_per_type'].get(file_type, 0) + 1
            stats['documents_per_term'][term] = \
                stats['documents_per_term'].get(term, 0) + 1
            stats['total_size'] += size
        
        return stats
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Statistiken: {str(e)}")
        return {}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)