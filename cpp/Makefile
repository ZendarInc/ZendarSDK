# Compilers
CXX = g++
C = $(CXX)
PROTOC = protoc

ZENDAR_PROTO_PATH=/usr/include/zendar
ZENDAR_HEADER_PATH=/usr/include/zendar
ZENDAR_INSTALL_PATH=/usr/lib
ZENDAR_CORE_DEB=$(wildcard zendar-core*.deb)
ZENDAR_API_DEB=$(wildcard zendar-zenapi*.deb)

LIBS = zendar_api glog zenproto protobuf shannon_core nng pthread
LINKFLAGS = $(addprefix -l, ${LIBS})
LIBPATH=$(addprefix -L, ${ZENDAR_INSTALL_PATH})
.PHONY: all install debian protocol example clean

all: install example

install: protocol

debian:
	dpkg -i ${ZENDAR_CORE_DEB}
	dpkg -i ${ZENDAR_API_DEB}

protocol: debian
	${PROTOC} -I=${ZENDAR_PROTO_PATH} --cpp_out=${ZENDAR_PROTO_PATH} ${ZENDAR_PROTO_PATH}/*.proto
	${PROTOC} -I=${ZENDAR_PROTO_PATH} --python_out=${ZENDAR_PROTO_PATH} ${ZENDAR_PROTO_PATH}/*.proto
	${CXX} -fPIC ${ZENDAR_PROTO_PATH}/*.pb.cc -shared -lprotobuf -o ${ZENDAR_INSTALL_PATH}/libzenproto.so
	cp ${ZENDAR_PROTO_PATH}/*.pb.h ${ZENDAR_INSTALL_PATH}

example: example-simple example-receiver example-control

example-simple: example-simple.cc
	${CXX} $< -I${ZENDAR_HEADER_PATH} ${LIBPATH} ${LINKFLAGS} -o $@

example-receiver: example-receiver.cc
	${CXX} $< -I${ZENDAR_HEADER_PATH} ${LIBPATH} ${LINKFLAGS} -o $@

example-control: example-control.cc
	${CXX} $< -I${ZENDAR_HEADER_PATH} ${LIBPATH} ${LINKFLAGS} -o $@

clean:
	rm -f example-simple
	rm -f example-receiver
	rm -f example-control
