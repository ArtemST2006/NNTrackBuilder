from typing import Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connect")

    def disconnect(self, user_id: int):
        print(f"discon {user_id}")
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_message(self, user_id: int, message: dict):
        socket = self.active_connections.get(user_id)
        if socket:
            try:
                await socket.send_json(message)
            except Exception as e:
                self.disconnect(user_id)
        else:
            print(f"User {user_id} not found in active connections")

manager = ConnectionManager()