# Python Tools

This directory consists of a list of Python tools that is used to interact
with the Zendar data

## Install necessary dependencies

    $> apt-get install -y       \
        ffmpeg                  \
        python3-pip

    $> pip3 install -r requirements.txt

## Compile protobuffers

This only needs to be ran once unless the protobufs are updated

    $> pushd ..
    $> sh make_data_proto.sh
    $> popd

## Setup Python environment

Every time when a new shell is started, run

    $> pushd ..
    $> source environment.sh
    $> popd

to setup the Python environment
