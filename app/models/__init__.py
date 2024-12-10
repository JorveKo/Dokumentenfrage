"""
Models-Modul für Document Scraper.
Exportiert alle Datenmodelle für die Anwendung.
"""

from .schemas import (
    FileType,
    DocumentMetadata,
    ScrapingStatus,
    ScrapingStats,
    ScrapingRequest,
    PerformanceMetrics,
    DownloadResult,
    ProcessingResult,
    WebSocketMessage
)

__all__ = [
    'FileType',
    'DocumentMetadata',
    'ScrapingStatus',
    'ScrapingStats',
    'ScrapingRequest',
    'PerformanceMetrics',
    'DownloadResult',
    'ProcessingResult',
    'WebSocketMessage'
] 