from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}  # {user_id: websocket}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept connection and add to dict if not already connected."""
        if user_id in self.active_connections:
            await websocket.close(code=1008, reason="User already connected")
            return
        await websocket.accept()
        self.active_connections[user_id] = websocket
        await websocket.send_json({"message": f"WebSocket connected for user {user_id}"})

    def disconnect(self, user_id: int):
        """Remove from dict on disconnect."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_to_user(self, user_id: int, message):
        """Send a message to a specific user - accepts both string and dict"""

        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                if isinstance(message, str):
                    # If it's a string, try to parse as JSON
                    try:
                        message_dict = json.loads(message)
                        await websocket.send_json(message_dict)
                    except json.JSONDecodeError:
                        # If not valid JSON, send as simple message
                        await websocket.send_json({"message": message})
                elif isinstance(message, dict):
                    # If it's already a dict, send directly
                    await websocket.send_json(message)
                else:
                    # Handle other types by converting to string
                    await websocket.send_json({"message": str(message)})
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {str(e)}")
                # self.disconnect(user_id)
        else:
            logger.warning(f"User {user_id} not connected")

    async def broadcast(self, message: dict):
        """Send to all connected users (optional, if needed)."""
        disconnected = []
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(user_id)
        for user_id in disconnected:
            self.disconnect(user_id)

# Instantiate the manager (add this in create_fastapi_app or globally)
manager = WebSocketManager()