"""
File Processing Utilities.
Handhabt Dateioperationen und -validierung.
"""

import os
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime
import hashlib
from urllib.parse import urlparse

from app.config import SUPPORTED_FILE_TYPES

logger = logging.getLogger(__name__)

class FileProcessor:
    """Klasse für Dateiverarbeitung und -validierung"""
    
    def __init__(self):
        self.supported_types = SUPPORTED_FILE_TYPES
        
    def get_file_type(self, url: str, content_type: str) -> Optional[str]:
        """
        Ermittelt den Dateityp aus URL und Content-Type.
        
        Args:
            url: URL der Datei
            content_type: MIME-Type der Datei
            
        Returns:
            Optional[str]: Erkannter Dateityp oder None
        """
        try:
            # Versuche zuerst aus der URL zu erkennen
            path = urlparse(url).path
            extension = os.path.splitext(path)[1].lower().replace('.', '')
            
            if extension in self.supported_types:
                return extension
                
            # Prüfe Content-Type
            for file_type, mime_type in self.supported_types.items():
                if mime_type in content_type.lower():
                    return file_type
                    
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei der Dateityp-Erkennung: {str(e)}")
            return None
            
    async def is_valid_file(self, content: bytes, file_type: str) -> bool:
        """
        Überprüft, ob der Dateiinhalt valide ist.
        
        Args:
            content: Dateiinhalt als Bytes
            file_type: Erwarteter Dateityp
            
        Returns:
            bool: True wenn Datei valide ist
        """
        try:
            if not content or len(content) < 8:
                return False
                
            # Magic Numbers für verschiedene Dateitypen
            magic_numbers = {
                'pdf': b'%PDF',
                'doc': b'\xD0\xCF\x11\xE0',
                'docx': b'PK\x03\x04'
            }
            
            if file_type not in magic_numbers:
                return True  # Kein bekannter Magic Number Check
                
            return content.startswith(magic_numbers[file_type])
            
        except Exception as e:
            logger.error(f"Fehler bei der Dateivalidierung: {str(e)}")
            return False
            
    def generate_filename(self, url: str, timestamp: str = None) -> str:
        """
        Generiert einen eindeutigen Dateinamen.
        
        Args:
            url: URL der Datei
            timestamp: Optional timestamp string
            
        Returns:
            str: Generierter Dateiname
        """
        try:
            # Erstelle Basis-Namen aus URL
            base_name = urlparse(url).path.split('/')[-1]
            
            # Entferne ungültige Zeichen
            base_name = "".join(c for c in base_name if c.isalnum() or c in '.-_')
            
            # Füge Timestamp hinzu
            time_str = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Erstelle URL-Hash
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            
            return f"{time_str}_{url_hash}_{base_name}"
            
        except Exception as e:
            logger.error(f"Fehler bei der Dateinamensgenerierung: {str(e)}")
            # Fallback: Generiere generischen Namen
            return f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
    def get_file_size(self, file_path: Path) -> Optional[int]:
        """
        Ermittelt die Dateigröße.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            Optional[int]: Dateigröße in Bytes oder None bei Fehler
        """
        try:
            return file_path.stat().st_size
        except Exception as e:
            logger.error(f"Fehler beim Ermitteln der Dateigröße: {str(e)}")
            return None
            
    def cleanup_file(self, file_path: Path) -> bool:
        """
        Löscht eine Datei sicher.
        
        Args:
            file_path: Pfad zur zu löschenden Datei
            
        Returns:
            bool: True wenn erfolgreich gelöscht
        """
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Datei erfolgreich gelöscht: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Datei: {str(e)}")
            return False

# Globale Instanz
file_processor = FileProcessor()