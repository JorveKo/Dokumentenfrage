"""
Konstanten für den Document Scraper.
"""

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
CHUNK_SIZE = 8192  # Bytes f��r Streaming-Downloads
MEMORY_LIMIT = 1024 * 1024 * 1024  # 1GB Speicherlimit 