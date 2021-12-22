# ZendarSDK

ZendarSDK illustrates how to use the radar data products generated from the Zendar radar system.

## Data products
The Zendar radar system produces three concurrent real-time data streams. These are:

- High resolution radar images for stationary objects
    - Binary file name: `<radar_id>_images.pbs`
    - Protobuf message type: `Image`
- Point detections based on range-doppler processing
    - Binary file name: `<radar_id>_points.pbs`
    - Protobuf message type: `TrackerState`
- Vehicle positions
    - Binary file name: `vn200.pbs`
    - Protobuf message type: `Position`

## Interface
The data interface is documented in [protocol](protocol/data.proto). This interface is written in [Protocol Bufffers](https://developers.google.com/protocol-buffers). Protobuffers can be compiled into C++, Python and other languages to be integrated into your project.

Zendar binary protobuf streams are stored in the following format:
```
<8-byte header> | <4-byte message size> <message> | <4-byte message size> <message> | ....
```
Please see [RadarDataStreamer](python/viewer/radar_data_streamer.py) for an example implementation.
