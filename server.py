import test_pb2_grpc
import test_pb2
import grpc
import time
import queue
from concurrent import futures
import asyncio
import functools
import threading


queueList={}

def blockInput(loop):
    s=input(">>").split(':')
    if len(s)==2: 
        if queueList.get(s[0],None)!=None:
            queueList[s[0]].put(s[1])
            print ("\nSend message to %s"%s[0])
    loop.run_in_executor(None,functools.partial(blockInput,loop))

class justServer(test_pb2_grpc.pushServerServicer):
    """just Server""" 

    def justHello(self,re,conte):
        meta=conte.invocation_metadata()
        a=test_pb2.res(key="just Hello",bar="I'm server and i know you are No.%s"%meta[0].value) 
        return a

    def somethingNew(self,req,cont):
        a=test_pb2.res(key="newthing",bar="sads")
        print("\n============")
        print(cont.peer())
        print(cont.invocation_metadata())
        print(">>")
        idx=cont.invocation_metadata()[0].value
        que=queueList[str(idx)]=queue.Queue()
        while True:
            f=que.get()
            a.bar=f
            yield  a
        
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



    



