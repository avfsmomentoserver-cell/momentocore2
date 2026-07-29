"""WebSocket Hub for Real-time Updates"""
import asyncio
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .manager import ConnectionManager


router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Main WebSocket endpoint for real-time updates."""
    await manager.connect(websocket, client_id, "market_updates")
    
    try:
        while True:
            # Receive messages from client (e.g., subscription requests)
            data = await websocket.receive_text()
            
            # Echo back acknowledgment
            await manager.send_personal_message(
                {"type": "ack", "message": f"Received: {data}"},
                websocket
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id, "market_updates")
        print(f"Client {client_id} disconnected")


async def broadcast_signal(signal_data: Dict[str, Any]):
    """Broadcast trading signal to all connected clients."""
    message = {
        "type": "signal",
        "timestamp": datetime.utcnow().isoformat(),
        "data": signal_data
    }
    await manager.broadcast(message, "market_updates")


async def broadcast_alert(alert_data: Dict[str, Any]):
    """Broadcast system alert to all connected clients."""
    message = {
        "type": "alert",
        "timestamp": datetime.utcnow().isoformat(),
        "data": alert_data
    }
    await manager.broadcast(message, "system_alerts")
