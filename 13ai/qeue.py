from queue import Queue,Empty

client={}
q={}

def get_did(sid):
    global client
    for did,v in client.items():
        for typ,vv in v.items():
            if sid in vv:
                return did
    return 

def get_client(did):
    if did in client:
        return client[did]
    return
def check_client(sid,did,typ):
    global client
    if did not in client:
        client[did]={'source':set(),'dest':set()}
        q[did]=Queue()
    if sid not in client[did][typ]:
        client[did][typ].add(sid)
    
    print('Client:',client)
    if client[did]['source'] and client[did]['dest']:
        return True
    if not client[did]['source'] or not client[did]['dest']:
        return False

def remove_client(sid):
    global client
    for did,v in client.items():
        for typ,vv in v.items():
            if sid in vv:
                client[did][typ].remove(sid)
                q[did].queue.clear()

def put_data(did,data):
    global q
    q[did].put(data)
    print('Queue in',did)

def get_data(did):
    global q
    # print('Q',q)
    try:
        da=q[did].get_nowait()
        q[did].task_done()
        print('Queue out',da)
        return da
    except Empty:
        return