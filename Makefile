
*.py:*.proto
	python3 -m grpc_tools.protoc --python_out=. --grpc_python_out=. -I. test.proto