import asyncio
import websockets
import json
import qeue
import detection
from urllib.parse import urlparse, parse_qs

clients = {}
status = {}

# Send detection data periodically
async def background_sender(websocket, did):
    print('background sender', did)
    status[did] = True
    try:
        while status.get(did, False):
            client_info = qeue.get_client(did)
            if client_info and 'dest' in client_info:
                da = qeue.get_data(did)
                if not da:
                    await asyncio.sleep(0.001)
                    continue
                da.update({'did': did, 'status': True})
                await websocket.send(json.dumps({'type': 'server_response', 'data': da}))
                print('Send Detection', da)
            await asyncio.sleep(0.001)
    except websockets.ConnectionClosed:
        print("Connection closed during sending")

# Handle each connected client
async def handler(websocket):
    path = websocket.path
    query = urlparse(path).query
    query_params = parse_qs(query)

    did = query_params.get('did', [None])[0]
    user = query_params.get('user', [None])[0]
    sid = id(websocket)

    print(f"Client connected: {sid}, User: {user}, DID: {did}")

    qeue.add_client(sid, websocket, did, user)
    if user == 'dest':
        asyncio.create_task(background_sender(websocket, did))

    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                payload = data.get("data", {})
            except Exception as e:
                print("Invalid message format:", e)
                continue

            if msg_type == 'source':
                if qeue.check_client(sid, payload['did'], 'source'):
                    did = qeue.get_did(sid)
                    if not status.get(did, False):
                        asyncio.create_task(background_sender(websocket, did))
                        print("Background task started")

                    result = detection.detect(payload['img'], payload['img_w'], payload['img_h'], payload['timestamp'])
                    result = {'did': did, 'timestamp': payload['timestamp'], 'status': True, 'detections': result}
                    print("RESULT", result)
                    qeue.put_data(did, result)

                    await websocket.send(json.dumps({'type': 'server_response', 'data': {'status': True, 'received': payload}}))
                else:
                    await websocket.send(json.dumps({'type': 'server_response', 'data': {'status': False, 'received': payload}}))
                    print(f"Discard data from {sid}: {payload['did']} {payload['timestamp']}")

            elif msg_type == 'dest':
                print(f"Dest request from {sid}: {payload}")
                if qeue.check_client(sid, payload['did'], 'dest'):
                    asyncio.create_task(background_sender(websocket, payload['did']))

    except websockets.ConnectionClosed:
        print(f"Client disconnected: {sid}")
    finally:
        did = qeue.get_did(sid)
        status[did] = False
        qeue.remove_client(sid)

# Start WebSocket server
async def main():
    async with websockets.serve(handler, "0.0.0.0", 5000):
        print("WebSocket server running on port 5000...")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
