# ZendarSDK

ZendarSDK illustrates how to use the Zendar APIs to control the ZPU and receive
the imaging data.

## Building

**You will need to install the ZenAPI host packages before building
the code in this repo**. The host packages are provided by Zendar.

Follow these steps to build the example code.

```
mkdir build && cd build
cmake ..
make all -j $(nproc)
```

The built examples are in `build/bin`.
