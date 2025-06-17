import socketio
import eventlet
import qeue
import detection
from urllib.parse import parse_qs

# Create a Socket.IO server with CORS enabled
sio = socketio.Server(cors_allowed_origins='*', async_mode='eventlet')
app = socketio.WSGIApp(sio)

status = {}

# Background task to send data periodically to each client
def background_sender(did):
    print('background sender', did)
  
    global status
    status[did] = True
    while status[did]:
        clients = qeue.get_client(did)
        if clients and 'dest' in clients:  # Added safety check
            for sid in list(clients['dest']):
                da=qeue.get_data(did)
                if not da:
                    continue
                da.update({'did':did,'status':True})
                sio.emit('server_response', da, to=sid)
                print('Send Detection',da)

        eventlet.sleep(0.001)  # Use eventlet.sleep instead of asyncio.sleep

# Event handler for client connection
@sio.event
def connect(sid, environ):
    print(f'Client connected: {sid}')
    query = environ.get('QUERY_STRING', '')
    query_dict = parse_qs(query)
    
    did = query_dict.get('did', [None])[0]
    user = query_dict.get('user', [None])[0]
    print('Connect Info', user, did)
    if 'dest' and qeue.check_client(sid, did, user):
        # Start the background sender task using eventlet
        sio.start_background_task(background_sender, did)
  
# Event handler for client disconnection
@sio.event
def disconnect(sid):
    global status
    did=qeue.get_did(sid)
    status[did] = False
    qeue.remove_client(sid)
    print(f'Client disconnected: {sid}')

# Event handler for receiving data from client
@sio.event
def source(sid, data):
    if qeue.check_client(sid, data['did'], 'source'):
        did=qeue.get_did(sid)
        if not status[did]:
            # Use eventlet's background task instead of asyncio
            sio.start_background_task(background_sender, data['did'])
            print("Background task started")
        result=detection.detect(data['img'],data['img_w'],data['img_h'],data['timestamp'])
        result={'did':data['did'],'timestamp':data['timestamp'],'status':True,'detections':result}
        print('RESULT',result)
        qeue.put_data(data['did'], result)
        sio.emit('server_response', {'status': True, 'received': data}, to=sid)
    else:
        sio.emit('server_response', {'status': False, 'received': data}, to=sid)
        print(f'Discard data from {sid}: {data['did']} {data['timestamp']}')
    
@sio.event
def dest(sid, data):
    print(f'Request from {sid}: {data}')
    if qeue.check_client(sid, data['did'], 'dest'):
        # Start the background sender task
        sio.start_background_task(background_sender, data['did'])

if __name__ == '__main__':
    # Start the server on port 5000
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)