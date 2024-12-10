"""
WebSocket Handler für Echtzeit-Updates des Dashboards.
Verwaltet WebSocket-Verbindungen und sendet Status-Updates an Clients.
"""

import logging
import json
from typing import Set, Dict
from datetime import datetime
from fastapi import WebSocket
from dataclasses import dataclass
from app.core.scraper import scraper_engine
from app.database.manager import db_manager

logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    """JSON Encoder für datetime Objekte"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@dataclass
class WebSocketMessage:
    """Struktur für WebSocket-Nachrichten"""
    type: str
    data: dict

    def dict(self):
        return {
            "type": self.type,
            "data": self.data
        }

class WebSocketManager:
    """Verwaltet WebSocket-Verbindungen und Nachrichtenverteilung"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.client_info: Dict[WebSocket, dict] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Neue WebSocket-Verbindung herstellen"""
        try:
            await websocket.accept()
            self.active_connections.add(websocket)
            self.client_info[websocket] = {
                "id": client_id,
                "connected_at": datetime.now()
            }
            logger.info(f"Neue WebSocket-Verbindung: {client_id}")
            await self.send_initial_state(websocket)
        except Exception as e:
            logger.error(f"Fehler beim WebSocket-Connect: {str(e)}")
            
    async def disconnect(self, websocket: WebSocket):
        """WebSocket-Verbindung trennen"""
        try:
            self.active_connections.remove(websocket)
            client_id = self.client_info.get(websocket, {}).get("id", "unknown")
            self.client_info.pop(websocket, None)
            logger.info(f"WebSocket-Verbindung getrennt: {client_id}")
        except Exception as e:
            logger.error(f"Fehler beim WebSocket-Disconnect: {websocket}")
            
    async def send_initial_state(self, websocket: WebSocket):
        """Initialen Status an neuen Client senden"""
        try:
            message = WebSocketMessage(
                type="initial_state",
                data={
                    "scraping_status": scraper_engine.status.dict(),
                    "stats": (await db_manager.get_statistics()).dict(),
                    "connected_at": self.client_info[websocket]["connected_at"],
                    "client_id": self.client_info[websocket]["id"]
                }
            )
            await self._send_message(websocket, message.dict())
        except Exception as e:
            logger.error(f"Fehler beim Senden des initialen Status: {str(e)}")
            
    async def broadcast(self, message: WebSocketMessage):
        """Nachricht an alle verbundenen Clients senden"""
        disconnected = set()
        
        for websocket in self.active_connections:
            try:
                await self._send_message(websocket, message.dict())
            except Exception as e:
                logger.error(f"Fehler beim Broadcast: {str(e)}")
                disconnected.add(websocket)
                
        # Cleanup disconnected clients
        for websocket in disconnected:
            await self.disconnect(websocket)
            
    async def send_status_update(self, status_data: dict):
        """Status-Update an alle Clients senden"""
        message = WebSocketMessage(
            type="status_update",
            data=status_data
        )
        await self.broadcast(message)
        
    async def send_error(self, error_message: str):
        """Fehlermeldung an alle Clients senden"""
        message = WebSocketMessage(
            type="error",
            data={"message": error_message}
        )
        await self.broadcast(message)

    async def _send_message(self, websocket: WebSocket, message: dict):
        """Hilfsmethode zum Senden von Nachrichten"""
        try:
            json_str = json.dumps(message, cls=DateTimeEncoder)
            await websocket.send_text(json_str)
        except Exception as e:
            logger.error(f"Fehler beim Senden der Nachricht: {str(e)}")
            raise

# Globale WebSocket-Manager Instanz
websocket_manager = WebSocketManager()