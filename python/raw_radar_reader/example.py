from argparse import ArgumentParser
import numpy as np
import matplotlib.pyplot as plt

from acquisition import AcquisitionStreamModel
from reader import (
    RadarModuleReader,
    Calibration
)

def main():
    argp = ArgumentParser()
    argp.add_argument(
            '--root',
            required=True,
            help='Root directory where data is stored')
    argp.add_argument(
            '--calibration',
            required=True,
            help='Path to calibration file')
    args = argp.parse_args()

    # This is a wrapper for access to the saved data on disk
    model = AcquisitionStreamModel(args.root)

    # This iterates over the radar modules present in this acquisition
    # `module` is a sort of 'id' for the module
    # `radar` actually provides access to the data for this radar module
    for module in model.radar_modules:
        radar = model.radar_module(module)

        # RadarModuleReader returns `RadarFrame` objects, which wrap the data
        # and metadata in a convenient format
        frame = RadarModuleReader(radar)
        idx = 0
        for f in frame:
            print("Frame idx ", f.frame_idx, ". First chirp at time ", f.time_common[0,0])
            range_axis = f.range_axis()
            doppler_axis = f.doppler_axis()

            range_profile = np.fft.fft(f.data[:,0,0,:], axis=1)
            # I am not fully sure about the Doppler value labeling for each FFT bin here,
            # but the combination of the `fftshift` here and the `extent` parameter to
            # `plt.imshow()` lines up the 0 bin in the right place.
            # This needs to be re-visited from first principles
            range_doppler = np.fft.fftshift(np.fft.fft(range_profile, axis=0), axes=0)

            plt.imshow(np.log10(np.abs(range_doppler)),
                       extent=[range_axis[0], range_axis[-1], doppler_axis[-1], doppler_axis[0]],
                       aspect='auto')
            plt.xlabel('Range (m)')
            plt.ylabel('Doppler speed (m/s)')
            plt.show()

            idx += 1
            if (idx == 1):
                break

    # `Calibration` is a wrapper to the calibration values
    # To apply the coefficients: 
    # data_out = data_in / cal.gains
    # data_out = data_in * np.exp(-1j * channel_phase_angle)
    # data_out = data_in * np.exp(1j * 2 * pi * ramp_slope * time_offset * fast_time_index)
    cal = Calibration(args.calibration)
    print(cal.phases_rad)
    print(cal.gains)
    print(cal.delays_ps)


if __name__ == "__main__":
    main() 
