"""
Rate Limiting Utilities.
Kontrolliert die API-Zugriffshäufigkeit.
"""

import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

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
                logger.debug(f"Rate limit erreicht. Warte {wait_time:.2f} Sekunden")
                await asyncio.sleep(wait_time)
                
        self.requests.append(now)

# Globale Instanz
rate_limiter = RateLimiter(max_requests=10, time_window=1.0)