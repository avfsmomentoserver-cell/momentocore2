"""WebSocket Connection Manager"""
import asyncio
from typing import Dict, List, Optional
from fastapi import WebSocket


class ConnectionManager:
    """Manages active WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str, channel: str = "default"):
        """Accept and register a new connection."""
        await websocket.accept()
        
        if channel not in self.active_connections:
            self.active_connections[channel] = []
            
        self.active_connections[channel].append(websocket)
        print(f"Client {client_id} connected to {channel}")
        
    def disconnect(self, websocket: WebSocket, client_id: str, channel: str = "default"):
        """Remove a connection."""
        if channel in self.active_connections:
            self.active_connections[channel].remove(websocket)
            print(f"Client {client_id} disconnected from {channel}")
            
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific connection."""
        await websocket.send_json(message)
        
    async def broadcast(self, message: dict, channel: str = "default"):
        """Broadcast message to all connections in a channel."""
        if channel not in self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections[channel].remove(conn)
