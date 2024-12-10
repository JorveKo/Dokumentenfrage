# app/core/downloader.py
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
import aiohttp
import aiofiles
from tenacity import retry, stop_after_attempt, wait_exponential

from config import (
    DOWNLOADS_DIR, 
    REQUEST_TIMEOUT, 
    CHUNK_SIZE,
    MAX_RETRIES
)
from app.utils.file.file_processor import file_processor

logger = logging.getLogger(__name__)

class DocumentDownloader:
    """Handhabt das Herunterladen von Dokumenten"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._ensure_downloads_dir()
        
    def _ensure_downloads_dir(self):
        """Stellt sicher, dass der Downloads-Ordner existiert"""
        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        
    async def init_session(self):
        """Initialisiert die HTTP Session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def close_session(self):
        """Schließt die HTTP Session"""
        if self.session:
            await self.session.close()
            self.session = None
            
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def download(self, url: str, file_type: str) -> Optional[Dict]:
        """Lädt ein Dokument herunter mit automatischen Wiederholungsversuchen"""
        if not self.session:
            await self.init_session()
            
        try:
            async with self.session.get(
                url,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True
            ) as response:
                if response.status != 200:
                    logger.warning(f"Failed to download {url}: Status {response.status}")
                    return None
                    
                # Validiere Content-Type
                content_type = response.headers.get('content-type', '')
                if not self._is_valid_content_type(content_type, file_type):
                    logger.warning(f"Invalid content type for {url}: {content_type}")
                    return None
                    
                # Generiere Dateinamen
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = file_processor.generate_filename(url, timestamp)
                file_path = DOWNLOADS_DIR / f"{filename}.{file_type}"
                
                # Streame Download
                total_size = 0
                file_hash = hashlib.md5()
                
                async with aiofiles.open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                        await f.write(chunk)
                        total_size += len(chunk)
                        file_hash.update(chunk)
                        
                # Validiere heruntergeladene Datei
                if not await self._validate_downloaded_file(file_path, file_type):
                    logger.warning(f"Invalid file content for {url}")
                    await self._cleanup_invalid_file(file_path)
                    return None
                    
                return {
                    'url': url,
                    'local_path': str(file_path),
                    'content_type': content_type,
                    'size': total_size,
                    'timestamp': timestamp,
                    'hash': file_hash.hexdigest()
                }
                
        except Exception as e:
            logger.error(f"Error downloading {url}: {str(e)}")
            raise  # Retry wird durch den Decorator gehandhabt
            
    def _is_valid_content_type(self, content_type: str, file_type: str) -> bool:
        """Überprüft, ob der Content-Type zum erwarteten Dateityp passt"""
        expected_type = SUPPORTED_FILE_TYPES.get(file_type.lower())
        return expected_type and expected_type in content_type.lower()
        
    async def _validate_downloaded_file(self, file_path: Path, file_type: str) -> bool:
        """Validiert den Inhalt der heruntergeladenen Datei"""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                header = await f.read(8)  # Lese die ersten 8 Bytes
                
            # Überprüfe Magic Numbers
            magic_numbers = {
                'pdf': b'%PDF',
                'doc': b'\xD0\xCF\x11\xE0',
                'docx': b'PK\x03\x04'
            }
            
            expected_magic = magic_numbers.get(file_type.lower())
            if not expected_magic:
                return True  # Kein Magic Number Check für unbekannte Dateitypen
                
            return header.startswith(expected_magic)
            
        except Exception as e:
            logger.error(f"Error validating file {file_path}: {str(e)}")
            return False
            
    async def _cleanup_invalid_file(self, file_path: Path):
        """Löscht ungültige Dateien"""
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Cleaned up invalid file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {str(e)}")
            
    async def cleanup(self):
        """Räumt Ressourcen auf"""
        await self.close_session()

# Globale Downloader-Instanz
document_downloader = DocumentDownloader()