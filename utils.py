# utils.py
import os
import hashlib
import logging
import asyncio
from typing import List, Set, Dict, Optional
from datetime import datetime
from urllib.parse import urlparse
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.corpus import wordnet
import numpy as np
from config import DOMAIN_TERMS, SUPPORTED_FILE_TYPES

# NLTK Downloads
for package in ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']:
    try:
        nltk.download(package, quiet=True)
    except Exception as e:
        logging.error(f"Fehler beim Download von NLTK Package {package}: {e}")

class TextProcessor:
    """Klasse für Textverarbeitung und -analyse"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('german') + stopwords.words('english'))
        self.term_cache = {}
        
    def preprocess_text(self, text: str) -> List[str]:
        """Bereitet Text für die Analyse vor"""
        if not text:
            return []
            
        # Normalisierung und Tokenisierung
        text = text.lower()
        tokens = word_tokenize(text)
        
        # Entferne Stopwords und Sonderzeichen
        tokens = [
            token for token in tokens 
            if token not in self.stop_words and token.isalnum()
        ]
        
        return tokens
        
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Berechnet die Ähnlichkeit zwischen zwei Texten"""
        # Cache-Key erstellen
        cache_key = hashlib.md5((text1 + text2).encode()).hexdigest()
        
        if cache_key in self.term_cache:
            return self.term_cache[cache_key]
            
        try:
            # Tokenisierung
            tokens1 = self.preprocess_text(text1)
            tokens2 = self.preprocess_text(text2)
            
            if not tokens1 or not tokens2:
                return 0.0
                
            # Erstelle Vokabular und Vektoren
            vocab = list(set(tokens1 + tokens2))
            vec1 = self.text_to_vector(tokens1, vocab)
            vec2 = self.text_to_vector(tokens2, vocab)
            
            # Berechne Cosinus-Ähnlichkeit
            similarity = self.cosine_similarity(vec1, vec2)
            
            # Cache das Ergebnis
            self.term_cache[cache_key] = similarity
            
            return similarity
            
        except Exception as e:
            logging.error(f"Fehler bei der Ähnlichkeitsberechnung: {e}")
            return 0.0
            
    @staticmethod
    def text_to_vector(tokens: List[str], vocab: List[str]) -> np.ndarray:
        """Konvertiert Text in einen Häufigkeitsvektor"""
        vector = np.zeros(len(vocab))
        token_counts = {}
        
        for token in tokens:
            token_counts[token] = token_counts.get(token, 0) + 1
            
        for i, word in enumerate(vocab):
            vector[i] = token_counts.get(word, 0)
            
        return vector
        
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Berechnet die Cosinus-Ähnlichkeit zwischen zwei Vektoren"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(dot_product / (norm1 * norm2))
        
    def extract_keywords(self, text: str, top_n: int = 10) -> List[tuple]:
        """Extrahiert wichtige Keywords aus dem Text"""
        tokens = self.preprocess_text(text)
        
        # Zähle Worthäufigkeiten
        word_freq = {}
        for token in tokens:
            word_freq[token] = word_freq.get(token, 0) + 1
            
        # Sortiere nach Häufigkeit
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_words[:top_n]

class TermExpander:
    """Klasse für die intelligente Begriffserweiterung"""
    
    def __init__(self):
        self.domain_terms = DOMAIN_TERMS
        self.expansion_cache = {}
        
    def expand_term(self, term: str) -> Set[str]:
        """Erweitert einen Suchbegriff um verwandte Begriffe"""
        if term in self.expansion_cache:
            return self.expansion_cache[term]
            
        expanded_terms = {term}
        
        try:
            # WordNet-Synonyme
            for syn in wordnet.synsets(term, lang='deu'):
                expanded_terms.update(lemma.name() for lemma in syn.lemmas())
                
                # Verwandte Begriffe
                for related in syn.hypernyms() + syn.hyponyms():
                    expanded_terms.update(lemma.name() for lemma in related.lemmas())
                    
            # Domänenspezifische Erweiterungen
            for category, terms in self.domain_terms.items():
                if any(domain_term in term.lower() for domain_term in terms):
                    expanded_terms.update(self.get_domain_specific_terms(term, category))
                    
            # Cache das Ergebnis
            self.expansion_cache[term] = expanded_terms
            
        except Exception as e:
            logging.error(f"Fehler bei der Begriffserweiterung: {e}")
            
        return expanded_terms
        
    def get_domain_specific_terms(self, term: str, category: str) -> Set[str]:
        """Generiert domänenspezifische verwandte Begriffe"""
        specific_terms = set()
        
        prefixes = {
            'allgemein': ['analyse_', 'bericht_', 'doku_'],
            'rechtlich': ['recht_', 'gesetz_', 'paragraf_'],
            'technisch': ['tech_', 'spec_', 'ref_']
        }
        
        for prefix in prefixes.get(category, []):
            specific_terms.add(f"{prefix}{term}")
            
        return specific_terms

class FileProcessor:
    """Klasse für Dateiverarbeitung und -validierung"""
    
    @staticmethod
    def get_file_type(url: str, content_type: str) -> Optional[str]:
        """Ermittelt den Dateityp aus URL und Content-Type"""
        # Prüfe Content-Type
        for file_type, mime_type in SUPPORTED_FILE_TYPES.items():
            if mime_type in content_type.lower():
                return file_type
                
        # Fallback: Prüfe Dateiendung
        path = urlparse(url).path.lower()
        extension = os.path.splitext(path)[1][1:]
        
        return extension if extension in SUPPORTED_FILE_TYPES.keys() else None
        
    @staticmethod
    async def is_valid_file(content: bytes, file_type: str) -> bool:
        """Überprüft, ob der Dateiinhalt valide ist"""
        if not content:
            return False
            
        # Prüfe Dateiheader
        headers = {
            'pdf': b'%PDF',
            'doc': b'\xD0\xCF\x11\xE0',
            'docx': b'PK\x03\x04'
        }
        
        return content.startswith(headers.get(file_type, b''))
        
    @staticmethod
    def generate_filename(url: str, timestamp: datetime) -> str:
        """Generiert einen eindeutigen Dateinamen"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        time_str = timestamp.strftime("%Y%m%d_%H%M%S")
        return f"{time_str}_{url_hash}"

class PerformanceMonitor:
    """Klasse für Performance-Monitoring"""
    
    def __init__(self):
        self.start_time = None
        self.download_times = []
        self.processing_times = []
        self.error_count = 0
        
    def start_monitoring(self):
        """Startet das Performance-Monitoring"""
        self.start_time = datetime.now()
        
    def add_download_time(self, duration: float):
        """Fügt eine Download-Zeit hinzu"""
        self.download_times.append(duration)
        
    def add_processing_time(self, duration: float):
        """Fügt eine Verarbeitungszeit hinzu"""
        self.processing_times.append(duration)
        
    def increment_error_count(self):
        """Erhöht den Fehlerzähler"""
        self.error_count += 1
        
    def get_stats(self) -> Dict:
        """Gibt Performance-Statistiken zurück"""
        if not self.start_time:
            return {}
            
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'elapsed_time': elapsed_time,
            'avg_download_time': np.mean(self.download_times) if self.download_times else 0,
            'avg_processing_time': np.mean(self.processing_times) if self.processing_times else 0,
            'error_rate': self.error_count / len(self.download_times) if self.download_times else 0,
            'downloads_per_minute': len(self.download_times) / (elapsed_time / 60) if elapsed_time > 0 else 0
        }

class RateLimiter:
    """Klasse für API Rate Limiting"""
    
    def __init__(self, max_requests: int, time_window: float):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        
    async def acquire(self):
        """Wartet, bis ein Request erlaubt ist"""
        now = datetime.now()
        
        # Entferne alte Requests
        self.requests = [req_time for req_time in self.requests 
                        if (now - req_time).total_seconds() < self.time_window]
                        
        # Warte, wenn das Limit erreicht ist
        if len(self.requests) >= self.max_requests:
            wait_time = self.time_window - (now - self.requests[0]).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
                
        self.requests.append(now)

# Globale Instanzen
text_processor = TextProcessor()
term_expander = TermExpander()
file_processor = FileProcessor()
performance_monitor = PerformanceMonitor()
rate_limiter = RateLimiter(max_requests=10, time_window=1.0)