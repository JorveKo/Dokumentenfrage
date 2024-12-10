"""
Text Processing Utilities.
Enthält Funktionen für Textanalyse und -verarbeitung.
"""

import logging
import hashlib
import nltk
import numpy as np
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

class TextProcessor:
    """Klasse für Textverarbeitung und -analyse"""
    
    def __init__(self):
        self.stop_words = set()
        self.term_cache = {}
        self._initialize_nltk()
        
    def _initialize_nltk(self):
        """Initialisiert NLTK-Komponenten"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            self.stop_words = set(stopwords.words('german') + stopwords.words('english'))
            logger.info("NLTK erfolgreich initialisiert")
        except Exception as e:
            logger.error(f"Fehler bei NLTK-Initialisierung: {e}")
            self.stop_words = set()

    # ... [Rest der TextProcessor Klasse aus utils.py]

# Globale Instanz
text_processor = TextProcessor()