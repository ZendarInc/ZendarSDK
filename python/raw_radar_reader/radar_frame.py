import numpy as np

class RadarFrame(object):
    """ Convenient wrapper for a radar frame and metadata"""
    def __init__(self, intrinsic):
        """ Initialize from an IntrinsicRadar message"""
        # Helper
        profile = intrinsic.profile.profiles[0]
        frame = intrinsic.profile.frame

        # Scalar parameters, per frame
        self.fast_time_samples = profile.number_of_adc_samples
        self.adc_sample_rate = profile.digital_out_sample_rate * 1e3

        self.ramp_slope = profile.ramp_slope
        self.occupied_bandwidth = self.ramp_slope * (self.fast_time_samples * 1 / self.adc_sample_rate * 1e6)
        self.center_frequency = profile.start_frequency * 1e3 + self.ramp_slope * (profile.adc_start_time) + 1/2 * self.occupied_bandwidth
        
        self.pri = profile.ramp_end_time + profile.idle_time + profile.chirps[0].idle_time
        self.slow_time_samples = frame.number_of_loops * (frame.chirp_end_index - frame.chirp_start_index + 1)
        self.frame_period = frame.frame_periodicity

        # Frame index
        self.frame_index = -1

        # Num RX / TX
        self.num_rx = len(intrinsic.receive_antenna_config)
        self.num_tx = len(intrinsic.transmit_antenna_config)
        self.mimo_order = len(intrinsic.profile_simplified[0].chirps)

        self.rx_antennas = np.zeros((self.num_rx, 3), dtype=np.double)
        self.tx_antennas = np.zeros((self.num_tx, 3), dtype=np.double)
        for rx in intrinsic.receive_antenna_config:
            self.rx_antennas[int(np.log2(rx.id))] = np.array([rx.T.x, rx.T.y, rx.T.z])

        for tx in intrinsic.transmit_antenna_config:
            self.tx_antennas[int(np.log2(tx.id))] = np.array([tx.T.x, tx.T.y, tx.T.z])

        # Helpers
        self._number_of_loops = frame.number_of_loops
        self._loop_size = frame.chirp_end_index - frame.chirp_start_index + 1

        # 1-D array of timestamps for each chirp
        self.time_common = -1 * np.ones((frame.number_of_loops, len(profile.chirps)), dtype=np.double)

        ## MIMO parameters, per chirp
        self.tx_mode = -1 * np.ones((len(profile.chirps),), dtype=np.int32)
        self._tx_phases = np.nan * np.ones((len(profile.chirps), self.num_tx), dtype=np.double)

        simplified = intrinsic.profile_simplified[0]
        for (i,c) in enumerate(simplified.chirps):
            self.tx_mode[i] = c.tx_mode

        ## Data: Nchirps x Nfiring x Nrx x Nadc
        self.data = np.zeros((frame.number_of_loops, len(profile.chirps), self.num_rx, self.fast_time_samples), dtype=np.complex64)


    # `data` is an array of ChirpResponses
    def add_data(self, c_data, p_data):
        """ Add data for controller and peripheral"""
        for (idx, chirp) in enumerate(c_data):
            idx_l = int(idx / self._loop_size)
            idx_c = int(idx % self._loop_size)

            self.time_common[idx_l, idx_c] = chirp.timestamp.common
            for (rx,ant) in enumerate([chirp.rx0, chirp.rx1, chirp.rx2, chirp.rx3]):
                tmp = np.array(ant.IQ);
                self.data[idx_l, idx_c, rx].real = tmp & 0x0000FFFF;
                self.data[idx_l, idx_c, rx].imag = (tmp >> 16) & 0x0000FFFF;
            if (idx == 0):
                self.frame_idx = chirp.idx_frame

        for (idx, chirp) in enumerate(p_data):
            idx_l = int(idx / self._loop_size)
            idx_c = int(idx % self._loop_size)

            self.time_common[idx_l, idx_c] = chirp.timestamp.common
            for (rx,ant) in enumerate([chirp.rx0, chirp.rx1, chirp.rx2, chirp.rx3]):
                tmp = np.array(ant.IQ);
                self.data[idx_l, idx_c, rx+4].real = tmp & 0x0000FFFF;
                self.data[idx_l, idx_c, rx+4].imag = (tmp >> 16) & 0x0000FFFF;
            if (idx == 0):
                self.frame_idx = chirp.idx_frame


    def range_axis(self):
        """ Get range axis"""
        return np.linspace(0, self.adc_sample_rate * 3e8 / (2 * self.ramp_slope * 1e12), self.fast_time_samples, endpoint=False)


    def doppler_axis(self):
        """ Get doppler axis"""
        vres = 3e8 / (self.center_frequency * 1e6) / (2 * self.slow_time_samples * self.pri * 1e-6)
        doppler_end = self.slow_time_samples / 2 / self.mimo_order
        return np.linspace(-doppler_end, doppler_end, int(self.slow_time_samples / self.mimo_order), endpoint=False) * vres
