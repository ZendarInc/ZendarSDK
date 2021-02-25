import numpy as np

from acquisition import (
    SensorPbTxt,
)
from radar_pb2 import RadarCalibrationConfig
from radar_frame import RadarFrame


class Calibration(object):
    """ Wrapper class for easily accessing calibration parameters."""

    def __init__(self, path):
        """ Initialize from a path to a calibration.pt file"""
        self.proto = SensorPbTxt(path, RadarCalibrationConfig)
        self.calibration = self.proto._read()

        self.num_vx = len(self.calibration.calibration_coefficients)
        self.phases_rad = np.zeros((8, 6), dtype=np.float)
        self.gains = np.zeros((8, 6), dtype=np.float)
        self.delays_ps = np.zeros((8, 6), dtype=np.float)

        for ant in self.calibration.calibration_coefficients:
            rx = int(np.log2(ant.antenna))
            tx = int(np.log2(ant.tx_antenna))
            self.phases_rad[rx, tx] = ant.channel_phase_angle
            self.gains[rx, tx] = ant.channel_gain_ratio_linear
            self.delays_ps[rx, tx] = ant.time_offset * 1e12


class RadarStreamReader(object):
    """ Not yet a public facing class"""
    def __init__(self, radar):
        self.stream = radar.stream
        
        frame_helper = radar.intrinsic._read().profile.frame
        self.frame_length = frame_helper.number_of_loops * (frame_helper.chirp_end_index - frame_helper.chirp_start_index + 1)

        self.synced = False

    def __iter__(self):
        frame_idx = 0
        
        data = []
        for chirp in self.stream:
            if frame_idx == 0:
                frame_idx = chirp.idx_frame

            if not self.synced:
                print("WARN: Frame out of sync: ", frame_idx)
                if chirp.idx_frame == frame_idx:
                    continue
                else:
                    self.synced = True

            data.append(chirp)
            if len(data) == self.frame_length:
                yield data
                data = []


class RadarModuleReader(object):
    """ Reads from SensorPath objects and returns RadarFrames"""
    def __init__(self, streams):
        """ Initialize from an array of SensorPath objects"""
        self.controller = iter(RadarStreamReader(streams[0]))
        self.peripheral = iter(RadarStreamReader(streams[1]))
        self.intrinsic = streams[0].intrinsic._read()

    def __iter__(self):
        """ Iterate over generated RadarFrame objects"""
        for (c,p) in zip(self.controller, self.peripheral):
            while (c[0].idx_frame > p[0].idx_frame):
                print("WARN: Peripheral out of sync: ", p[0].idx_frame)
                p = next(self.peripheral)

            while (p[0].idx_frame > c[0].idx_frame):
                print("WARN: Controller out of sync: ", c[0].idx_frame)
                c = next(self.controller)

            assert (c[0].idx_frame == p[0].idx_frame)

            frame = RadarFrame(self.intrinsic)
            frame.add_data(c, p)
            yield frame
