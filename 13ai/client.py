import asyncio
import websockets
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebSocketSender")

async def continuous_sender(uri, interval=1):
    """Connect to WebSocket server and send data continuously"""
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Connected to {uri}")
                while True:
                    # Prepare your data to send
                    data = {
                        "timestamp": datetime.now().isoformat(),
                        "message": "Continuous data stream",
                        "counter": getattr(continuous_sender, "counter", 0)
                    }
                    continuous_sender.counter = data["counter"] + 1
                    
                    # Send the data
                    await websocket.send(json.dumps(data))
                    logger.info(f"Sent: {data}")
                    
                    # Wait before sending next message
                    await asyncio.sleep(interval)
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Error: {e}. Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    # Replace with your WebSocket server URI
    server_uri = "ws://127.0.0.1:8765"
    asyncio.run(continuous_sender(server_uri))