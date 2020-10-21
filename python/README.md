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

    $> sh make_data_proto.sh

## Setup Python environment

Every time when a new shell is started, run

    $> source environment.sh

to setup the Python environment
