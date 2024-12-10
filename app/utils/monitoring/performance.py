"""
Performance Monitoring Utilities.
Überwacht und analysiert System-Performance.
"""

import logging
from datetime import datetime
import numpy as np
from typing import Dict

logger = logging.getLogger(__name__)

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
        logger.info("Performance-Monitoring gestartet")
        
    def add_download_time(self, duration: float):
        """
        Fügt eine Download-Zeit hinzu
        
        Args:
            duration: Dauer des Downloads in Sekunden
        """
        self.download_times.append(duration)
        
    def add_processing_time(self, duration: float):
        """
        Fügt eine Verarbeitungszeit hinzu
        
        Args:
            duration: Dauer der Verarbeitung in Sekunden
        """
        self.processing_times.append(duration)
        
    def increment_error_count(self):
        """Erhöht den Fehlerzähler"""
        self.error_count += 1
        
    def get_stats(self) -> Dict:
        """
        Gibt Performance-Statistiken zurück
        
        Returns:
            Dict: Performance-Metriken
        """
        if not self.start_time:
            return {}
            
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        total_downloads = len(self.download_times)
        
        stats = {
            'elapsed_time': elapsed_time,
            'total_downloads': total_downloads,
            'error_count': self.error_count,
            'avg_download_time': np.mean(self.download_times) if self.download_times else 0,
            'avg_processing_time': np.mean(self.processing_times) if self.processing_times else 0,
            'error_rate': self.error_count / total_downloads if total_downloads > 0 else 0,
            'downloads_per_minute': total_downloads / (elapsed_time / 60) if elapsed_time > 0 else 0
        }
        
        logger.debug(f"Performance-Statistiken erstellt: {stats}")
        return stats
        
    def reset(self):
        """Setzt alle Metriken zurück"""
        self.start_time = None
        self.download_times.clear()
        self.processing_times.clear()
        self.error_count = 0
        logger.info("Performance-Metriken zurückgesetzt")

# Globale Instanz
performance_monitor = PerformanceMonitor()