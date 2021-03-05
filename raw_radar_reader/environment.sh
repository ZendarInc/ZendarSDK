export PYTHONPATH=${PYTHONPATH}:${PWD}/protocol
export PYTHONPATH=${PYTHONPATH}:${PWD}/python

pushd protocol
protoc primitive.proto --python_out .
protoc radar.proto --python_out .
protoc acquisition.proto --python_out .
popd
