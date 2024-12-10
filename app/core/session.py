"""
Scraping Session Management.
Verwaltet den Zustand und die Metriken einer einzelnen Scraping-Sitzung.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Set

@dataclass
class ScrapingSession:
    """
    Speichert den Zustand und die Metriken einer Scraping-Session.
    
    Attributes:
        term (str): Der Suchbegriff für diese Session
        file_type (str): Typ der zu suchenden Dateien (z.B. 'pdf')
        max_results (int): Maximale Anzahl der zu verarbeitenden Ergebnisse
        similarity_threshold (float): Schwellenwert für Textähnlichkeit
        start_time (datetime): Startzeitpunkt der Session
        processed_urls (Set[str]): Bereits verarbeitete URLs
        successful_downloads (int): Anzahl erfolgreicher Downloads
        failed_downloads (int): Anzahl fehlgeschlagener Downloads
        total_bytes (int): Gesamtgröße der heruntergeladenen Dateien
    """
    
    term: str
    file_type: str
    max_results: int
    similarity_threshold: float
    start_time: datetime
    processed_urls: Set[str] = field(default_factory=set)  # Fix hier
    successful_downloads: int = 0
    failed_downloads: int = 0
    total_bytes: int = 0
    
    def __post_init__(self):
        """Initialisiert das Set für verarbeitete URLs nach der Objekterstellung."""
        if self.processed_urls is None:
            self.processed_urls = set()
            
    def add_processed_url(self, url: str) -> None:
        """
        Fügt eine URL zu den verarbeiteten URLs hinzu.
        
        Args:
            url (str): Die zu speichernde URL
        """
        self.processed_urls.add(url)
        
    def get_stats(self) -> dict:
        """
        Gibt aktuelle Session-Statistiken zurück.
        
        Returns:
            dict: Dictionary mit Session-Statistiken
        """
        duration = (datetime.now() - self.start_time).total_seconds()
        return {
            'term': self.term,
            'file_type': self.file_type,
            'successful_downloads': self.successful_downloads,
            'failed_downloads': self.failed_downloads,
            'total_bytes': self.total_bytes,
            'duration': duration,
            'processed_urls': len(self.processed_urls)
        }