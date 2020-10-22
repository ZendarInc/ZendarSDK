# ZendarSDK

ZendarSDK illustrates how to use the radar data products generated from the Zendar radar system.

## Data products
The Zendar radar system produces three concurrent real-time data streams. These are

- high resolution radar images for stationary objects. This file is named `<radar_id>_images.pbs`.
- point detections based on range-doppler processing. This file is named `<radar_id>_points.pbs`.
- vehicle positions. This file is named `vn200.pbs`.

## Interface
The data interface is documented in [protocol](protocol). This interface is written in [Protocol Bufffers](https://developers.google.com/protocol-buffers). Protobuffers can be compiled into C++, Python and other languages to be integrated into your project.

Please see [here](protobuf/README.md) for the interface descriptions.

## Data Viewer
Recorded data can be played back by the Python based viewer. Please follow the instructions [here](python/viewer).



