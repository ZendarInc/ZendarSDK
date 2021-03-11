# Python Tools

This directory consists of a list of Python tools that is used to interact
with the Zendar data
- `viewer` contains tools that can visualize processed SAR images and point
  clouds from the Zendar radar system
- `raw_radar_reader` contains tools for interacting with raw radar data
  (ADC samples) directly

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

## Setup

### One-time setup

These tools depend on the debian files contained in `ZendarSDK/cpp`. First you must
build the portion of those dependencies that are needed by this tool. The first time
you do this, you may need to install the required C++ dependencies specified in
`ZendarSDK/cpp/README`.
```
pushd ../cpp
sudo make protocol
popd
```

### Every time you open a new terminal

When you open a new terminal, set your environment variables using this script:
```
source environment.sh
```
