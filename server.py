import test_pb2_grpc
import test_pb2
import grpc
import queue
from concurrent import futures
import sys
import asyncio
import functools
import threading
import logging
import enum
logging.basicConfig(format='%(asctime)s %(message)s (%(funcName)s)', level=logging.DEBUG)


class clientContext():
    _instance = None
    __clientStatusList = {}
    __infoQueueList = {}
    __nameList = []

    def __new__(cls, *args, **kwargs):
        if cls._instance == None:
            cls._instance = super(clientContext, cls).__new__(cls, *args, **kwargs)
            logging.info("创建新的客户端上下文对象 %s"%cls._instance)
        return cls._instance

    def isNameAvailable(self, name):
        if name in self.__nameList:
            return True
        return False

    def addClient(self, name, subscribeContext ):
        logging.info("创建客户端(%s)"%name)
        self.__clientStatusList[name] = clientStatus(
            subscribeContext,functools.partial(self.loseDestructor,name))

        self.__clientStatusList[name].startCounting()

        self.__infoQueueList[name] = queue.Queue()

        self.__nameList.append(name)

    def removeClient(self, name):
        if not self.isNameAvailable(name):
            logging.error("要访问的客户端不存在")
            return

        self.__clientStatusList.pop(name)
        self.__infoQueueList.pop(name)
        self.__nameList.remove(name)

    def putInfoQ(self, name, info):
        if not self.isNameAvailable(name):
            logging.error("要访问的客户端不存在")
            return None
        return self.__infoQueueList[name].put(info)

    def getInfQ(self, name):
        if not self.isNameAvailable(name):
            logging.error("要访问的客户端不存在")
            return None
        return self.__infoQueueList[name].get()

    def clearStatus(self,name):
        if not self.isNameAvailable(name):
            logging.error("要访问的客户端不存在")
            return None
        self.__clientStatusList[name].clearStatus()

    def listClients(self):
        return  self.__nameList

    def loseDestructor(self,name):
        logging.warning("客户端:%s离线,执行清除操作"%name)

        self.putInfoQ(name,"KILL")

        self.removeClient(name)

class clientStatus():
    def __init__(self,  subscribeContext,loseCallback):
        self.statusQueue = queue.Queue()
        self.subscribeContext = subscribeContext
        self.counterThread = None
        self.loseCallback=loseCallback

    def is_alive(self):
        if self.statusQueue.qsize() > 3:
            return False
        return True

    def clearStatus(self):
        with self.statusQueue.mutex:
            self.statusQueue.queue.clear()

    def checker(self):
        logging.debug("增加状态计数")
        self.statusQueue.put(True)
        if not (self.is_alive()):
            logging.info("客户端离线:停止计数器线程")
            self.counterThread.cancel()
            self.loseCallback()
            try:
                self.subscribeContext.abort(grpc.StatusCode.UNAVAILABLE,"heartbeat counter overflow, we assume client is disconnect")
            except Exception:
                logging.info("中止订阅%s"%Exception)
            return 
        self.counterThread = threading.Timer(1, self.checker)
        self.counterThread.start()

    def startCounting(self):
        logging.info("状态计数线程开始工作")
        self.counterThread = threading.Timer(1, self.checker)
        self.counterThread.start()


def blockInput(loop):
    s = input(">>")
    ccObj = clientContext()
    if len(s.split(':')) == 2:
        s = s.split(':')
        if ccObj.isNameAvailable(s[0]):
            ccObj.putInfoQ(s[0], s[1])
            print("Send message to %s" % s[0])
    elif(s == 'list'):
        print("Subscribed List:")
        print("---------------------------------")
        for n, i in enumerate(ccObj.listClients()):
            print("\t %d:%s" % (n+1, i))

    loop.run_in_executor(None, functools.partial(blockInput, loop))


class justServer(test_pb2_grpc.pushServerServicer):
    """just Server"""

    def __init__(self):
        self.ccObj = clientContext()


    def subscribe(self, req, cont):
        print("Get Subscribed")
        print(cont.peer())
        sys.stdout.write(">>")
        sys.stdout.flush()
        if not self.ccObj.isNameAvailable(req.name):
            self.ccObj.addClient(req.name,cont)
            self.ccObj.putInfoQ(req.name,"Subscribe OK")
        else:#出现该种情况说明有可能是在服务端的半连接周期时客户端发生了重连.
            logging.warning("客户端(%s)在半连接周期内发生重连!"%req.name)
            return 
        while self.ccObj.isNameAvailable(req.name):
            yield test_pb2.response(info=self.ccObj.getInfQ(req.name))

    def heartbeat(self, req, cont):
        while True:
            name = req.next().name
            logging.debug("receive heartbeat:%s" % name)

            if not self.ccObj.isNameAvailable(name):
                logging.error("client has not subscribed. name:%s " % name)
                cont.abort(grpc.StatusCode.UNAVAILABLE,"Heart beat before subscribe")
                return

            else:
                self.ccObj.clearStatus(name)
                

            yield test_pb2.heartbeatRes(status=True)


def server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    test_pb2_grpc.add_pushServerServicer_to_server(justServer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    while True:
        pass


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, functools.partial(blockInput, loop))
    loop.run_in_executor(None, server)
    loop.run_forever()
