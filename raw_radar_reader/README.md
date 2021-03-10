# Raw Radar Interface

This directory contains tools for interacting with raw radar data. Zendar
makes available raw ADC samples from our FMCW radars. The example tools
in this directory allow researchers to easily use this data format.

o## Dependencies
```
libprotobuf
protobuf-compiler
```

Python packages:
```
pip3 install -r requirements.txt
```

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

## Example Script

```
python3 ./python/example.py --root <path-to-data> --calibration <path-to-cal-file>
```

This example script loads the requested data, plots a range-Doppler spectrum, and
then reports the calibration contents of the specified file.

## RadarFrame Format

| Attribute           | Description                                    |
| ------------------- | ---------------------------------------------- |
| fast\_time\_samples | Number of fast time (range) samples per chirp  |
| adc\_sample\_rate   | Frequency (Hz) of the ADC                      |
| ramp\_slope         | Chirp ramp slope (MHz/us)                      |
| occupied\_bandwidth | Occupied chirp bandwidth (MHz)                 |
| center\_frequency   | Chirp center frequency (MHz)                   |
| pri                 | Pulse repetition interval (us)                 |
| slow\_time\_samples | Number of slow time samples (chirps per frame) |
| frame\_period       | Frame period (ms)                              |
|                     |                                                |
| frame\_index        | A frame ID                                     |
| time\_common        | A frame timestamp                              |
|                     |                                                |
| num\_rx             | Number of RX antennas on the radar             |
| num\_tx             | Number of TX antennas on the radar             |
| mimo\_order         | MIMO order                                     |
| rx\_antennas        | (x,y,z) coordinates of RX antennas             |
| tx\_antennas        | (x,y,z) coordinates of TX antennas             |
| tx\_mode            | MIMO firing mode (if bit i is set, TX i fired) |
| tx\_phases          | Not implemented yet (data is TDM)              |
|                     |                                                |
| data                | Complex data                                   |

The data shape is (Nloops, mimo\_order, num\_rx, fast\_time\_samples).
