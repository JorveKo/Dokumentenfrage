# app/websockets.py
"""
WebSocket Handler für Echtzeit-Updates des Dashboards.
Verwaltet WebSocket-Verbindungen und sendet Status-Updates an Clients.
"""

import logging
import asyncio
import json
from typing import Dict, Set
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed

from app.core.scraper import scraper_engine
from app.database import db_manager
from models import WebSocketMessage

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Verwaltet alle aktiven WebSocket-Verbindungen"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.client_info: Dict[WebSocket, dict] = {}
        self.update_task: asyncio.Task = None
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Verbindet einen neuen WebSocket-Client"""
        try:
            await websocket.accept()
            self.active_connections.add(websocket)
            self.client_info[websocket] = {
                'id': client_id,
                'connected_at': datetime.now(),
                'last_update': datetime.now()
            }
            
            logger.info(f"Neue WebSocket-Verbindung: {client_id}")
            
            # Starte Update-Task falls noch nicht laufend
            if not self.update_task or self.update_task.done():
                self.update_task = asyncio.create_task(self._periodic_updates())
                
        except Exception as e:
            logger.error(f"Fehler beim WebSocket-Connect: {str(e)}")
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                
    async def disconnect(self, websocket: WebSocket):
        """Trennt eine WebSocket-Verbindung"""
        try:
            self.active_connections.remove(websocket)
            client_info = self.client_info.pop(websocket, {})
            logger.info(f"WebSocket-Verbindung getrennt: {client_info.get('id', 'unknown')}")
            
            # Stoppe Update-Task wenn keine Verbindungen mehr aktiv
            if not self.active_connections and self.update_task:
                self.update_task.cancel()
                
        except Exception as e:
            logger.error(f"Fehler beim WebSocket-Disconnect: {str(e)}")
            
    async def broadcast(self, message: dict):
        """Sendet eine Nachricht an alle verbundenen Clients"""
        disconnected = set()
        
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
                self.client_info[websocket]['last_update'] = datetime.now()
                
            except ConnectionClosed:
                disconnected.add(websocket)
            except Exception as e:
                logger.error(f"Fehler beim Broadcast an {self.client_info[websocket]['id']}: {str(e)}")
                disconnected.add(websocket)
                
        # Cleanup getrennte Verbindungen
        for websocket in disconnected:
            await self.disconnect(websocket)
            
    async def _periodic_updates(self):
        """Sendet regelmäßige Status-Updates an alle Clients"""
        try:
            while self.active_connections:
                # Sammle aktuelle Status-Informationen
                scraping_status = scraper_engine.status
                stats = await db_manager.get_statistics()
                
                # Erstelle Update-Nachricht
                message = WebSocketMessage(
                    type="status_update",
                    data={
                        "scraping_status": scraping_status.dict(),
                        "stats": stats.dict(),
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                # Sende Update an alle Clients
                await self.broadcast(message.dict())
                
                # Warte bis zum nächsten Update
                await asyncio.sleep(1)  # 1 Sekunde Update-Intervall
                
        except asyncio.CancelledError:
            logger.info("Periodic updates stopped")
        except Exception as e:
            logger.error(f"Fehler in periodic_updates: {str(e)}")
            
    async def send_error(self, websocket: WebSocket, error_message: str):
        """Sendet eine Fehlermeldung an einen spezifischen Client"""
        try:
            message = WebSocketMessage(
                type="error",
                data={"message": error_message}
            )
            await websocket.send_json(message.dict())
            
        except Exception as e:
            logger.error(f"Fehler beim Senden der Fehlermeldung: {str(e)}")
            
    async def send_notification(self, websocket: WebSocket, notification: str, level: str = "info"):
        """Sendet eine Benachrichtigung an einen spezifischen Client"""
        try:
            message = WebSocketMessage(
                type="notification",
                data={
                    "message": notification,
                    "level": level
                }
            )
            await websocket.send_json(message.dict())
            
        except Exception as e:
            logger.error(f"Fehler beim Senden der Benachrichtigung: {str(e)}")

# Globale WebSocket-Manager Instanz
websocket_manager = WebSocketManager()

async def handle_websocket(websocket: WebSocket, client_id: str):
    """Haupthandler für WebSocket-Verbindungen"""
    try:
        await websocket_manager.connect(websocket, client_id)
        
        # Sende initiales Status-Update
        message = WebSocketMessage(
            type="initial_state",
            data={
                "scraping_status": scraper_engine.status.dict(),
                "stats": (await db_manager.get_statistics()).dict()
            }
        )
        await websocket.send_json(message.dict())
        
        # Warte auf Nachrichten vom Client
        while True:
            try:
                data = await websocket.receive_json()
                
                # Verarbeite Client-Nachrichten
                if data.get('type') == 'ping':
                    await websocket.send_json({
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat()
                    })
                    
            except WebSocketDisconnect:
                await websocket_manager.disconnect(websocket)
                break
                
    except Exception as e:
        logger.error(f"Fehler in handle_websocket: {str(e)}")
        try:
            await websocket_manager.disconnect(websocket)
        except:
            pass

# FastAPI WebSocket Route
from app import app

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await handle_websocket(websocket, client_id)