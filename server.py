import test_pb2_grpc
import test_pb2
import grpc
import time
import queue
from concurrent import futures
import sys
import asyncio
import functools
import threading
queueList={}

def blockInput(loop):
    s=input(">>")
    if len(s.split(':'))==2: 
        s=s.split(':')
        if queueList.get(s[0],None)!=None:
            queueList[s[0]].put(s[1])
            print ("Send message to %s"%s[0])
    elif(s=='list'):
        print("Subscribed List:")
        print("---------------------------------")
        for n,i in enumerate(queueList.keys()):
            print("\t %d:%s"%(n+1,i))

    loop.run_in_executor(None,functools.partial(blockInput,loop))

class justServer(test_pb2_grpc.pushServerServicer):
    """just Server""" 
    def subscribe(self,req,cont):
        print("Get Subscribed")
        print(cont.peer())
        sys.stdout.write(">>")
        sys.stdout.flush()

        if queueList.get(req.name,None)==None:
            queueList[req.name]=queue.Queue()
        que=queueList[req.name]

        while True:
            yield  test_pb2.response(info=que.get())
        
def server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    test_pb2_grpc.add_pushServerServicer_to_server(justServer(),server)
    server.add_insecure_port('[::]:50051')
    server.start()
    while True:
        pass


if __name__=="__main__":
    loop=asyncio.get_event_loop()
    loop.run_in_executor(None,functools.partial(blockInput,loop))
    loop.run_in_executor(None,server)
    loop.run_forever()



    



