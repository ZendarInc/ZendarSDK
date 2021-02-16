# Python Tools

This directory consists of a list of Python tools that is used to interact
with the Zendar data

## Install necessary dependencies

    $> apt-get install -y       \
        ffmpeg                  \
        python3-pip             \
        protobuf-compiler

    $> pip3 install --upgrade pip
    $> pip3 install -r requirements.txt

## Compile protobuffers

The protobufs are compiled and installed as part of the C++ installation
process, so please run that if you have not already.

## Setup Python environment

Every time when a new shell is started, run

    $> pushd ..
    $> source environment.sh
    $> popd

to setup the Python environment
