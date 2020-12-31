# grpc-python-server-push-example

>**WARNING!**
>I do not know if this is the correct way to implement server push.

1. Construct a stream-stream connection.

2. In client-side, pass the id of client via metadata. The stub should return an iterator, and call `next()` method of this method will block cause server has not responsed yet.

3. In server-side, when it receives the first request, construct a new `Queue`. Then, blocking reading this queue by `Queue.get()`. Once some new data is written into this queue, server will raise a response to client. In this example, writter is a standard `input`  which is invoked in another thread.

![screenshot](https://github.com/CNLHC/grpc-python-server-push-example/blob/master/screenshoot.gif)
