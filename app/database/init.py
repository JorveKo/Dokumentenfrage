"""
Datenbank-Modul für Document Scraper.
Handhabt alle Datenbankoperationen und -verbindungen.
"""

from .manager import DatabaseManager, db_manager

__all__ = ['DatabaseManager', 'db_manager'] 