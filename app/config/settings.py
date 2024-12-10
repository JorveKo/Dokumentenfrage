"""
Hauptkonfiguration für den Document Scraper.
Enthält alle grundlegenden Einstellungen.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env Datei laden
load_dotenv()

# Basis-Verzeichnis
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Ordnerstruktur
DOWNLOADS_DIR = BASE_DIR / "downloads"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
LOGS_DIR = BASE_DIR / "logs"

# API Konfiguration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('SEARCH_ENGINE_ID')

# Datenbankeinstellungen
MONGODB_URI = os.getenv('MONGODB_URI', "mongodb://mongodb:27017/")
DB_NAME = "document_scraper"

# Logo-Einstellungen
LOGO_FILE = STATIC_DIR / "images" / "logo.png"

# Scraper-Einstellungen
MAX_PARALLEL_DOWNLOADS = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.85
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30
BATCH_SIZE = 10

# Cache-Einstellungen
CACHE_ENABLED = True
CACHE_DURATION = 3600  # 1 Stunde 