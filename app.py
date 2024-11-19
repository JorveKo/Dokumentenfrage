import os
import logging
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from scraper import DocumentScraper
from dotenv import load_dotenv

# Lade Umgebungsvariablen aus der .env-Datei
load_dotenv()

# API-Schlüssel aus Umgebungsvariablen
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# FastAPI-Anwendung initialisieren
app = FastAPI()

# Statische Dateien und Templates einbinden
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Logging einrichten
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Scraper-Instanz erstellen
scraper = DocumentScraper(GOOGLE_API_KEY, GOOGLE_CSE_ID)


@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Dashboard anzeigen"""
    return templates.TemplateResponse("index.html", {"request": {}})


@app.post("/api/start")
async def api_start_scraping(term: str, file_type: str, max_results: int = 10):
    """Startet den Scraping-Prozess"""
    results = scraper.search_documents(term, file_type, max_results)
    return {"status": "success", "results": results}
