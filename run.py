"""
Startet den Document Scraper Server.
Verwendung: python run.py
"""

import uvicorn
from app import app

if __name__ == "__main__":
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=5000, 
        reload=True,
        log_level="info"
    ) 