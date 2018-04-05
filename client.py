import grpc
import test_pb2
import test_pb2_grpc
import datetime
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser = argparse.ArgumentParser(description='Description of your program')
parser.add_argument('-n', '--name', help='name of this client',
                    required=True, type=str)

def ChannelMonitor(ChannelConnectivity):
    print(ChannelConnectivity)

def run(name):
    channel = grpc.insecure_channel("localhost:50051")

    channel.subscribe(ChannelMonitor)

    stub = test_pb2_grpc.pushServerStub(channel)

    responser = stub.subscribe(test_pb2.clientInfo(name=name))
    
    while True:
        print(responser.next().info)


if __name__ == '__main__':
    args = vars(parser.parse_args())
    name = args['name']
    run(name)
