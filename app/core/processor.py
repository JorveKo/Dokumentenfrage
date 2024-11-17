# app/core/processor.py
import logging
import asyncio
from typing import Optional, Dict
from datetime import datetime
import hashlib

import aiofiles
from langdetect import detect

from config import DOWNLOADS_DIR, SUPPORTED_FILE_TYPES
from app.database import db_manager
from utils import text_processor, file_processor

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Verarbeitet und analysiert heruntergeladene Dokumente"""
    
    async def process(
        self,
        doc_info: Dict,
        term: str,
        similarity_threshold: float,
        snippet: str
    ) -> bool:
        """Verarbeitet ein heruntergeladenes Dokument"""
        try:
            # Basis-Validierung
            if not await self._validate_document(doc_info):
                return False
                
            # Extrahiere Metadaten
            metadata = await self._extract_metadata(doc_info, term, snippet)
            
            # Prüfe auf Duplikate
            if await self._is_duplicate(metadata, similarity_threshold):
                logger.info(f"Duplikat gefunden für: {doc_info['url']}")
                await self._cleanup_duplicate(doc_info['local_path'])
                return False
                
            # Speichere in Datenbank
            if await db_manager.store_document(metadata):
                logger.info(f"Dokument erfolgreich verarbeitet: {doc_info['url']}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Fehler bei der Dokumentverarbeitung: {str(e)}")
            await self._cleanup_failed(doc_info['local_path'])
            return False
            
    async def _validate_document(self, doc_info: Dict) -> bool:
        """Validiert ein Dokument"""
        try:
            file_path = DOWNLOADS_DIR / doc_info['local_path']
            
            # Prüfe Dateigröße
            if not await self._check_file_size(file_path):
                return False
                
            # Prüfe Dateiformat
            if not await self._verify_file_format(file_path, doc_info['content_type']):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei der Dokumentvalidierung: {str(e)}")
            return False
            
    async def _extract_metadata(self, doc_info: Dict, term: str, snippet: str) -> Dict:
        """Extrahiert Metadaten aus dem Dokument"""
        try:
            # Basis-Metadaten
            metadata = {
                'url': doc_info['url'],
                'local_path': str(DOWNLOADS_DIR / doc_info['local_path']),
                'content_type': doc_info['content_type'],
                'size': doc_info['size'],
                'timestamp': datetime.now().isoformat(),
                'term': term,
                'file_type': file_processor.get_file_type(doc_info['url'], 
                                                        doc_info['content_type'])
            }
            
            # Erweiterte Metadaten
            metadata.update({
                'keywords': await self._extract_keywords(snippet),
                'language': await self._detect_language(snippet),
                'hash': self._calculate_hash(snippet),
                'download_time': doc_info.get('download_time', 0)
            })
            
            return metadata
            
        except Exception as e:
            logger.error(f"Fehler bei der Metadaten-Extraktion: {str(e)}")
            return {}
            
    async def _check_file_size(self, file_path: str) -> bool:
        """Überprüft die Dateigröße"""
        try:
            size = file_path.stat().st_size
            min_size = 100  # 100 Bytes
            max_size = 100 * 1024 * 1024  # 100 MB
            
            return min_size <= size <= max_size
            
        except Exception as e:
            logger.error(f"Fehler bei der Größenprüfung: {str(e)}")
            return False
            
    async def _verify_file_format(self, file_path: str, content_type: str) -> bool:
        """Verifiziert das Dateiformat"""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                header = await f.read(8)  # Lese die ersten 8 Bytes
                
            file_type = file_processor.get_file_type(str(file_path), content_type)
            if not file_type:
                return False
                
            # Überprüfe Magic Numbers
            magic_numbers = {
                'pdf': b'%PDF',
                'doc': b'\xD0\xCF\x11\xE0',
                'docx': b'PK\x03\x04'
            }
            
            return header.startswith(magic_numbers.get(file_type, b''))
            
        except Exception as e:
            logger.error(f"Fehler bei der Formatverifizierung: {str(e)}")
            return False
            
    async def _is_duplicate(self, metadata: Dict, similarity_threshold: float) -> bool:
        """Prüft, ob das Dokument ein Duplikat ist"""
        try:
            # Prüfe exakte Duplikate über Hash
            existing_doc = await db_manager.get_document_by_hash(metadata['hash'])
            if existing_doc:
                return True
                
            # Prüfe ähnliche Dokumente
            similar_docs = await db_manager.get_similar_documents(
                metadata['term'],
                metadata['hash']
            )
            
            for doc in similar_docs:
                similarity = text_processor.calculate_similarity(
                    metadata.get('snippet', ''),
                    doc.get('snippet', '')
                )
                if similarity > similarity_threshold:
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Fehler bei der Duplikatsprüfung: {str(e)}")
            return False
            
    async def _extract_keywords(self, text: str) -> list:
        """Extrahiert Keywords aus dem Text"""
        try:
            keywords = text_processor.extract_keywords(text)
            return [keyword for keyword, _ in keywords]
        except Exception as e:
            logger.error(f"Fehler bei der Keyword-Extraktion: {str(e)}")
            return []
            
    async def _detect_language(self, text: str) -> str:
        """Erkennt die Sprache des Textes"""
        try:
            return detect(text)
        except:
            return 'unknown'
            
    def _calculate_hash(self, text: str) -> str:
        """Berechnet einen Hash für den Text"""
        return hashlib.md5(text.encode()).hexdigest()
        
    async def _cleanup_duplicate(self, file_path: str):
        """Löscht duplizierte Dateien"""
        try:
            full_path = DOWNLOADS_DIR / file_path
            if full_path.exists():
                full_path.unlink()
        except Exception as e:
            logger.error(f"Fehler beim Cleanup des Duplikats: {str(e)}")
            
    async def _cleanup_failed(self, file_path: str):
        """Löscht fehlgeschlagene Downloads"""
        try:
            full_path = DOWNLOADS_DIR / file_path
            if full_path.exists():
                full_path.unlink()
        except Exception as e:
            logger.error(f"Fehler beim Cleanup: {str(e)}")

# Globale Prozessor-Instanz
document_processor = DocumentProcessor()