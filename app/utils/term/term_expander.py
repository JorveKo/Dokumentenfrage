"""
Term Expansion Utilities.
Erweitert Suchbegriffe um verwandte Terme.
"""

import logging
from typing import Set, Dict
import nltk
from nltk.corpus import wordnet
from app.config import DOMAIN_TERMS

logger = logging.getLogger(__name__)

class TermExpander:
    """Klasse für die intelligente Begriffserweiterung"""
    
    def __init__(self):
        self.domain_terms = DOMAIN_TERMS
        self.expansion_cache: Dict[str, Set[str]] = {}
        self._initialize_nltk()
        
    def _initialize_nltk(self):
        """Initialisiert die benötigten NLTK-Komponenten"""
        try:
            nltk.download('wordnet', quiet=True)
            nltk.download('omw-1.4', quiet=True)  # Open Multilingual WordNet
            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
            logger.info("NLTK Daten erfolgreich geladen")
        except Exception as e:
            logger.error(f"Fehler beim Download der NLTK Daten: {str(e)}")
            raise RuntimeError("NLTK Initialisierung fehlgeschlagen")
    
    def expand_term(self, term: str) -> Set[str]:
        """Erweitert einen Suchbegriff um verwandte Begriffe"""
        try:
            # Basis-Set mit dem Original-Term
            expanded_terms = {term}
            
            # Domänenspezifische Erweiterungen
            expanded_terms.update(self.get_domain_specific_terms(term, 'allgemein'))
            
            # Versuche WordNet-Erweiterungen
            try:
                for syn in wordnet.synsets(term, lang='deu'):
                    expanded_terms.update(lemma.name() for lemma in syn.lemmas())
            except Exception as e:
                logger.warning(f"WordNet-Erweiterung nicht möglich: {str(e)}")
            
            return expanded_terms
        
        except Exception as e:
            logger.error(f"Fehler bei der Begriffserweiterung für '{term}': {str(e)}")
            return {term}  # Fallback zum Original-Term
        
    def get_domain_specific_terms(self, term: str, category: str) -> Set[str]:
        """
        Generiert domänenspezifische Begriffserweiterungen.
        
        Args:
            term: Ursprünglicher Begriff
            category: Domänenkategorie
            
        Returns:
            Set[str]: Domänenspezifische Erweiterungen
        """
        specific_terms = set()
        
        # Basis-Erweiterungen
        prefixes = {
            'allgemein': ['analyse_', 'bericht_', 'doku_'],
            'rechtlich': ['recht_', 'gesetz_', 'paragraf_'],
            'technisch': ['tech_', 'spec_', 'ref_']
        }
        
        # Füge Präfix-Varianten hinzu
        for prefix in prefixes.get(category, []):
            specific_terms.add(f"{prefix}{term}")
            
        # Füge domänenspezifische Kombinationen hinzu
        if category in self.domain_terms:
            specific_terms.update(
                f"{term}_{domain_term}" 
                for domain_term in self.domain_terms[category]
            )
            specific_terms.update(
                f"{domain_term}_{term}" 
                for domain_term in self.domain_terms[category]
            )
                
        return specific_terms
        
    def clear_cache(self):
        """Leert den Erweiterungs-Cache"""
        self.expansion_cache.clear()
        logger.debug("Term-Expansion Cache geleert")

# Globale Instanz
term_expander = TermExpander()

if __name__ == "__main__":
    print("Testing TermExpander...")
    expander = TermExpander()
    test_term = "Vertrag"
    expanded = expander.expand_term(test_term)
    print(f"Original term: {test_term}")
    print(f"Expanded terms: {expanded}")