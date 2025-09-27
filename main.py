# Main entry point for the application.

import asyncio
from dotenv import load_dotenv
from app.websocket_client import BinanceWebSocketClient
from app.reporting import Reporting

# Load environment variables from .env file
load_dotenv()

async def main():
    """
    Main function to start the Binance WebSocket client and the reporting service.
    """
    client = BinanceWebSocketClient()
    reporting = Reporting()

    # Create tasks for the WebSocket client and the reporting scheduler
    websocket_task = asyncio.create_task(client.run())
    reporting_task = asyncio.create_task(reporting.run_scheduler())

    # Run both tasks concurrently
    await asyncio.gather(
        websocket_task,
        reporting_task
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application shutting down.")