from typing import Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connected via WebSocket")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User {user_id} disconnected")

    async def send_message(self, user_id: str, message: dict):
        socket = self.active_connections.get(user_id)
        if socket:
            try:
                await socket.send_json(message)
            except Exception as e:
                print(f"Error sending to {user_id}: {e}")
                self.disconnect(user_id)
        else:
            # Это нормально, если пользователь уже ушел
            print(f"User {user_id} not found in active connections")

manager = ConnectionManager()