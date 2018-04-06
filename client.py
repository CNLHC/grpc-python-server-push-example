import grpc
import test_pb2
import test_pb2_grpc
import datetime
import argparse
import threading
import time
import logging

logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO)


class heartbeatThread(threading.Thread):
    def __init__(self, stub, clientName):
        threading.Thread.__init__(self)
        self.stub = stub
        self.clientName = clientName

    def run(self):
        logging.info("开始发送心跳包")
        m= self.stub.heartbeat(self.heartbeatGenerator())
        while True:
            logging.debug("收到心跳包响应:%s"%m.next())

    def heartbeatGenerator(self):
        while True:
            yield test_pb2.heartbeatReq(name=self.clientName)
            time.sleep(2)


def ChannelMonitor(ChannelConnectivity):
    print(ChannelConnectivity)


def run(name):
    time.sleep(3)#解决客户端在半连接周期内重连的问题...每次都等待超过一个半连接周期后再进行链接

    channel = grpc.insecure_channel("47.95.205.174:50051")

    channel.subscribe(ChannelMonitor)


    stub = test_pb2_grpc.pushServerStub(channel)

    responser = stub.subscribe(test_pb2.clientInfo(name=name))
    logging.info("订阅成功!%s"%responser.next())

    heartbeatThread(stub, name).start()

    while True:
        print(responser.next().info)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-n', '--name', help='name of this client',
                        required=True, type=str)
    args = vars(parser.parse_args())
    name = args['name']
    run(name)
