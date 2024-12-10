"""
Logging-Konfiguration für den Document Scraper.
"""

import logging
import os

# Logging Konfiguration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DIR = 'logs'

# Stelle sicher, dass das Log-Verzeichnis existiert
os.makedirs(LOG_DIR, exist_ok=True)

# Logging Setup
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(f'{LOG_DIR}/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__) 