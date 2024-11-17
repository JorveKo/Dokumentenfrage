# app/core/__init__.py
"""
Core Module für die Hauptfunktionalität des Document Scrapers.
Enthält die zentrale Logik für Scraping, Downloads und Dokumentenverarbeitung.
"""

from .scraper import scraper_engine
from .downloader import document_downloader
from .processor import document_processor

__version__ = '2.0.0'

__all__ = [
    'scraper_engine',
    'document_downloader',
    'document_processor',
]