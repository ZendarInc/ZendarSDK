#!/bin/sh

src_dir=./protocol
dst_dir=./protocol

mkdir -p $dst_dir
protoc -I=$src_dir --python_out=$dst_dir $src_dir/data.proto
