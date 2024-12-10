"""
WebSocket Routen für das Dashboard.
Definiert die WebSocket-Endpoints für Echtzeit-Kommunikation.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import logging
import json
from .handler import websocket_manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket Endpoint für Client-Verbindungen.
    
    Handhabt:
    - Initiale Verbindung
    - Ping/Pong für Connection-Keeping
    - Status-Updates
    - Fehlerbehandlung
    - Saubere Trennung
    
    Args:
        websocket: WebSocket Verbindung
        client_id: Eindeutige Client-ID
    """
    try:
        # Verbindung herstellen
        await websocket_manager.connect(websocket, client_id)
        logger.info(f"WebSocket Verbindung hergestellt für Client: {client_id}")
        
        # Hauptloop für Client-Kommunikation
        while True:
            try:
                # Warte auf Client-Nachrichten
                data = await websocket.receive_json()
                
                # Verarbeite verschiedene Nachrichtentypen
                message_type = data.get('type', '')
                
                if message_type == 'ping':
                    # Ping-Pong zur Verbindungsaufrechterhaltung
                    await websocket.send_json({
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat(),
                        'client_id': client_id
                    })
                    
                elif message_type == 'request_status':
                    # Client fordert Status-Update an
                    await websocket_manager.send_status_update({
                        'client_id': client_id,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                else:
                    logger.warning(f"Unbekannter Nachrichtentyp von Client {client_id}: {message_type}")
                    
            except WebSocketDisconnect:
                # Handle normale Verbindungstrennung
                logger.info(f"Client {client_id} hat die Verbindung getrennt")
                await websocket_manager.disconnect(websocket)
                break
                
            except json.JSONDecodeError:
                # Handle ungültige JSON-Nachrichten
                logger.error(f"Ungültige JSON-Nachricht von Client {client_id}")
                await websocket_manager.send_error("Ungültiges Nachrichtenformat")
                
            except Exception as e:
                # Handle unerwartete Fehler
                logger.error(f"Fehler bei der Verarbeitung der Nachricht von Client {client_id}: {str(e)}")
                await websocket_manager.send_error("Interner Server-Fehler")
                
    except Exception as e:
        # Handle Verbindungsfehler
        logger.error(f"Kritischer Fehler für Client {client_id}: {str(e)}")
        try:
            await websocket_manager.disconnect(websocket)
        except:
            pass
        
    finally:
        # Stelle sicher, dass die Verbindung in jedem Fall getrennt wird
        try:
            await websocket_manager.disconnect(websocket)
        except:
            pass
        logger.info(f"WebSocket-Verbindung beendet für Client: {client_id}") 