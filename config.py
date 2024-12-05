# config.py
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# .env Datei laden
load_dotenv()
# Basis-Verzeichnis
BASE_DIR = Path(__file__).resolve().parent

# Ordnerstruktur
DOWNLOADS_DIR = BASE_DIR / "downloads"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
LOGS_DIR = BASE_DIR / "logs"

# Erstelle notwendige Ordner
for directory in [DOWNLOADS_DIR, STATIC_DIR, TEMPLATES_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API Konfiguration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('SEARCH_ENGINE_ID')

# Datenbankeinstellungen
mongodb_uri = os.getenv('MONGODB_URI')
logger.info(f"Loaded MONGODB_URI from env: {mongodb_uri}")
DB_NAME = "document_scraper"
MONGODB_URI = mongodb_uri or "mongodb://mongodb:27017/"
logger.info(f"Using MONGODB_URI: {MONGODB_URI}")
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

# Logging-Einstellungen
LOG_FILE = LOGS_DIR / "scraper.log"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = "INFO"

# Unterstützte Dateitypen
SUPPORTED_FILE_TYPES = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

# Matrix-Dashboard Einstellungen
MATRIX_COLORS = {
    'primary': '#00ff00',    # Matrix Grün
    'background': '#000000', # Schwarz
    'dark': '#001100',      # Dunkelgrün
    'text': '#00ff00',      # Matrix Grün
    'highlight': '#00aa00'  # Helleres Grün
}

# Domain-spezifische Begriffe
DOMAIN_TERMS = {
    'allgemein': [
        "vertrag", "analyse", "dokument", "bericht", "handbuch",
        "anleitung", "spezifikation", "dokumentation"
    ],
    'rechtlich': [
        "gesetz", "verordnung", "richtlinie", "paragraph",
        "rechtsprechung", "urteil", "beschluss"
    ],
    'technisch': [
        "manual", "guide", "specification", "documentation",
        "protocol", "standard", "reference"
    ]
}

# API Kostenberechnung
API_COST_PER_REQUEST = 0.005

# Performance-Einstellungen
CHUNK_SIZE = 8192  # Bytes für Streaming-Downloads
MEMORY_LIMIT = 1024 * 1024 * 1024  # 1GB Speicherlimit