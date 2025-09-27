# This module will handle the connection to the Binance WebSocket.

import asyncio
import json
import websockets
from .config import BINANCE_WEBSOCKET_URL
from .data_processor import DataProcessor

class BinanceWebSocketClient:
    """
    Connects to the Binance WebSocket and processes incoming ticker data.
    """
    def __init__(self):
        self.url = BINANCE_WEBSOCKET_URL
        self.data_processor = DataProcessor()

    async def run(self):
        """
        Connects to the WebSocket and listens for messages indefinitely.
        """
        while True:
            try:
                async with websockets.connect(self.url) as websocket:
                    print("Connected to Binance WebSocket.")
                    await self.listen(websocket)
            except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError) as e:
                print(f"Connection error: {e}. Reconnecting in 10 seconds...")
                await asyncio.sleep(10)
            except Exception as e:
                print(f"An unexpected error occurred: {e}. Reconnecting in 10 seconds...")
                await asyncio.sleep(10)

    async def listen(self, websocket):
        """
        Listens for incoming messages and passes them to the data processor.
        """
        async for message in websocket:
            data = json.loads(message)
            await self.data_processor.process_message(data)