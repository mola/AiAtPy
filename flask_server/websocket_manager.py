# websocket_manager.py
import asyncio
import websockets
from websockets.exceptions import ConnectionClosed

class WebSocketManager:
    def __init__(self):
        self.clients = set()

    async def register(self, websocket):
        self.clients.add(websocket)
        print(f"Client connected: {id(websocket)}")

    async def unregister(self, websocket):
        self.clients.discard(websocket)
        print(f"Client disconnected: {id(websocket)}")

    async def handle_client(self, websocket):
        counter = 0
        try:
            while True:
                counter += 1
                await websocket.send(f"Message #{counter} from server")
                await asyncio.sleep(2)
        except ConnectionClosed:
            pass

    # Change this method to accept a single argument
    async def handler(self, websocket):
        await self.register(websocket)
        try:
            await self.handle_client(websocket)
        finally:
            await self.unregister(websocket)