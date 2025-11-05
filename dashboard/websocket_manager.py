"""
WebSocket Manager for CEO Discovery Dashboard

Manages WebSocket connections and broadcasts real-time updates
for CEO Discovery events (new proposals, patterns, status changes).
"""
from fastapi import WebSocket
from typing import List, Dict
import asyncio
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts CEO Discovery updates"""

    def __init__(self):
        """Initialize WebSocket manager with empty connection list"""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accept new WebSocket connection and send welcome message.

        Args:
            websocket: The WebSocket connection to accept
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

        # Send connection established message
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "message": "Connected to CEO Discovery live updates"
        })

    def disconnect(self, websocket: WebSocket):
        """
        Remove WebSocket connection from active list.

        Args:
            websocket: The WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict):
        """
        Broadcast message to all connected clients.

        Args:
            message: Dictionary containing the message to broadcast
        """
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_new_proposal(self, proposal: Dict):
        """
        Broadcast new proposal event to all clients.

        Args:
            proposal: Dictionary containing proposal data
        """
        await self.broadcast({
            "type": "new_proposal",
            "proposal": proposal,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })

    async def broadcast_pattern_discovered(self, pattern: Dict):
        """
        Broadcast pattern discovery event to all clients.

        Args:
            pattern: Dictionary containing pattern data
        """
        await self.broadcast({
            "type": "pattern_discovered",
            "pattern": pattern,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })

    async def broadcast_status_change(self, status: str):
        """
        Broadcast status change event to all clients.

        Args:
            status: New status string (e.g., "active", "idle", "analyzing")
        """
        await self.broadcast({
            "type": "status_change",
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })

    async def broadcast_pain_point_identified(self, pain_point: Dict):
        """
        Broadcast pain point identification event to all clients.

        Args:
            pain_point: Dictionary containing pain point data
        """
        await self.broadcast({
            "type": "pain_point_identified",
            "pain_point": pain_point,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })
