#!/bin/sh

#Install debian packages
dpkg -i zendar_core*.deb
dpkg -i zendar_zenapi*.deb

#Install protobufs
src_dir=/usr/include/zenproto
dst_dir=/usr/lib

protoc -I=$src_dir --cpp_out=$src_dir $src_dir/*.proto
g++ -fPIC $src_dir/*.pb.cc -shared -o $dst_dir/libzenproto.so
cp $src_dir/*.pb.h $dst_dir

# build example program
g++ main.cc -I/usr/lib -L/usr/lib -lzendar_api -lglog  -lzenproto  -lprotobuf  -lshannon_core -lnng -lpthread -o prog
