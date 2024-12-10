"""
WebSocket-Modul für Echtzeit-Updates des Dashboards.
"""

from .handler import websocket_manager
from ..routes import router

__all__ = ['websocket_manager', 'router']