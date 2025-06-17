from socketio import Client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SocketIOClient")

sio = Client()

@sio.event
def connect():
    logger.info("Connected to Socket.IO server")

@sio.event
def disconnect():
    logger.info("Disconnected from Socket.IO server")

@sio.event
def message(data):
    logger.info(f"Received message: {data}")

def send_data_continuously():
    counter = 0
    while True:
        try:
            counter += 1
            data = {"count": counter, "timestamp": "your_data_here"}
            sio.emit('message', data)  # 'message' is the event name
            logger.info(f"Sent: {data}")
            sio.sleep(1)  # Wait 1 second
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            sio.sleep(5)  # Wait before reconnecting

if __name__ == "__main__":
    sio.connect('http://127.0.0.1:5000')  # Your Socket.IO server URL
    try:
        send_data_continuously()
    except KeyboardInterrupt:
        pass
    finally:
        sio.disconnect()