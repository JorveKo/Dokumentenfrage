"""
Konfigurations-Modul für Document Scraper.
Zentraler Zugangspunkt für alle Konfigurationseinstellungen.
"""

# Erst logging importieren, da andere Module den Logger nutzen könnten
from .logging import LOG_LEVEL, LOG_FORMAT, LOG_DIR, logger

# Dann die anderen Module
from .settings import (
    BASE_DIR, DOWNLOADS_DIR, STATIC_DIR, TEMPLATES_DIR, LOGS_DIR,
    GOOGLE_API_KEY, GOOGLE_CSE_ID, MONGODB_URI, DB_NAME,
    LOGO_FILE, MAX_PARALLEL_DOWNLOADS, DEFAULT_SIMILARITY_THRESHOLD,
    MAX_RETRIES, REQUEST_TIMEOUT, BATCH_SIZE, CACHE_ENABLED,
    CACHE_DURATION
)

from .constants import (
    SUPPORTED_FILE_TYPES, MATRIX_COLORS, DOMAIN_TERMS,
    API_COST_PER_REQUEST, CHUNK_SIZE, MEMORY_LIMIT
)

__all__ = [
    'LOG_LEVEL', 'LOG_FORMAT', 'LOG_DIR', 'logger',
    'BASE_DIR', 'DOWNLOADS_DIR', 'STATIC_DIR', 'TEMPLATES_DIR', 'LOGS_DIR',
    'GOOGLE_API_KEY', 'GOOGLE_CSE_ID', 'MONGODB_URI', 'DB_NAME',
    'LOGO_FILE', 'MAX_PARALLEL_DOWNLOADS', 'DEFAULT_SIMILARITY_THRESHOLD',
    'MAX_RETRIES', 'REQUEST_TIMEOUT', 'BATCH_SIZE', 'CACHE_ENABLED',
    'CACHE_DURATION',
    'SUPPORTED_FILE_TYPES', 'MATRIX_COLORS', 'DOMAIN_TERMS',
    'API_COST_PER_REQUEST', 'CHUNK_SIZE', 'MEMORY_LIMIT'
] 