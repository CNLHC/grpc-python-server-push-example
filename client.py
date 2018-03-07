import grpc
import test_pb2
import test_pb2_grpc
import datetime
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser = argparse.ArgumentParser(description='Description of your program')
parser.add_argument('-i', '--id', help='ID of this client',
                    required=True, type=int)


def genReq():
    a = [test_pb2.req(foo="bar")]
    for i in a:
        yield i


def run(idx):
    channel = grpc.insecure_channel("localhost:50051")
    stub = test_pb2_grpc.pushServerStub(channel)
    m = stub.justHello(test_pb2.req(
        foo="foo"), metadata=(("index", str(idx)),))
    print(m)
    m = stub.somethingNew(genReq(), metadata=(("index", str(idx)),))
    for i in m:
        print(i)

if __name__ == '__main__':
    args = vars(parser.parse_args())
    ID = args['id']
    run(ID)
