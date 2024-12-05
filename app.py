import os
import logging
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core.scraper import scraper_engine  # Verwende die Core-Version
from app.routes import router
from app.websockets import websocket_manager
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

# Router und WebSocket Handler einbinden
app.include_router(router)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    logger.debug(f"New WebSocket connection from client {client_id}")
    try:
        await websocket_manager.connect(websocket, client_id)
        logger.debug(f"Client {client_id} connected successfully")
        while True:
            data = await websocket.receive_json()
            logger.debug(f"Received message from client {client_id}: {data}")
            await websocket_manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        logger.debug(f"Client {client_id} disconnected")
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in websocket connection: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
