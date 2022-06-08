# ZendarSDK

ZendarSDK illustrates how to use the Zendar APIs to control the ZPU and receive
the imaging data.

## Building

**You will need to install the host packages before building
the code in this repo.** Please refer to the Software and Operating manual
for how to download and install the Zendar host package.

Follow these steps to build the example code.

```
mkdir build && cd build
cmake ..
make all -j $(nproc)
```

The built examples are in `build/bin`.

## ZenAPI
Please refer to [ZenAPI](https://github.com/ZendarInc/ZendarSDK/wiki/ZenAPI)

## Protobuf Structure Definition
Please refer to [ZenProto](https://github.com/ZendarInc/ZendarSDK/wiki/Protobuf-Definitions)
