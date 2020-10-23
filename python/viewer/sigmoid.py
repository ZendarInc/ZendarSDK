import numpy as np
from collections import deque
import logging as LOG

class Sigmoid(object):
    """
    First applies log10, then uses a tanh sigmoid function,
    adjusted with a quadratic on its input, to re-scale magnitudes
    of a RADAR image with the objective of maximizing useful
    dynamic range, and rejecting background clutter. Using statistics
    and a moving average history, it's output is intended to
    be easy to interpret and pleasing to the human eye.

    The 2nd order polynomial inside the tanh sigmoid adjusts the sigmoid to
    pass through three points, defining the points where the sigmoid output
    is equal to a lower point (default=0.05), 0.5, and and upper point
    (default=0.95.)

    The lowest value, is intended to be near the "noise floor"
    (typically, defined by ground clutter, rather than noise in the RF system.)
    For most automotive images, the vast majority of the pixels are ground
    clutter, so the median and standard deviation of the whole image mostly
    characterize this clutter. The median is doing the main work here, but
    it is expected that depending on the environment, the standard deviation
    could vary, so if we consider self.lower to be the beginning of the pass
    band, adding some buffer to the median proportional to the standard
    deviation is sensible. With sigma_buffer set to 0.5, this does not have
    a very strong effect; the importance of this buffer is mostly speculative
    at this point.

    Setting the mid point (sigmoid output = 0.5) based on a (fairly high)
    percentile gave good results.

    Both lower and mid are set using moving averages to avoid rapid changes
    frame by frame.

    The upper value is set to a constant offset from the mid point;
    if there are a couple really bright objects in the scene, it is undesirable
    to waste the available output dynamic range on them at the expense of
    the rest of the scene.
    """
    def __init__(self,
                 # percentile of log10 image to set to midpoint of output range
                 mid_percentile=99,
                 # multiple of standard deviation to add to median to set
                 # bottom part of output range (self.lower)
                 sigma_buffer=0.5,
                 # minimum log10 difference between self.mid and self.lower
                 min_mid_buffer=1.0,
                 # log10 difference between self.mid and
                 # upper part of output range
                 upper_buffer=1.5,
                 # value of output range corresponding to self.lower
                 lower_out=0.05,
                 # value of output range corresponding to self.mid+upper_buffer
                 upper_out=0.95,
                 # window size for moving average
                 # (median and standard deviation)
                 history_size=20,
                 # minimum value to clip input before applying log10
                 # to avoid error with zero or negative magnitude values
                 pre_log_min=1e-9):

        self.mid_percentile = mid_percentile
        self.sigma_buffer = sigma_buffer
        self.min_mid_buffer = min_mid_buffer
        self.upper_buffer = upper_buffer
        self.lower_out = lower_out
        self.upper_out = upper_out
        self.pre_log_min = pre_log_min
        self.log_min = np.log10(pre_log_min)
        self.lower = MovingAverage(history_size)
        self.mid = MovingAverage(history_size)

    def __call__(self, vals):
        # clip out zero and negative values and apply log10
        log_vals = np.log10(np.clip(a=vals,
                                    a_min=self.pre_log_min,
                                    a_max=None))
        # update self.lower and self.mid with new statistics of log_vals
        self.update_statistics(log_vals)
        if self.lower.is_valid() and self.mid.is_valid():
            # fit polynomial input to sigmoid
            self.fit_sigmoid()
            # return adjusted sigmoid
            return self.adjusted_sigmoid(log_vals)
        return vals

    def update_statistics(self, vals):
        vals_masked_flat = vals[vals > self.log_min].flatten()
        if not len(vals_masked_flat):
            LOG.warning("all data below threshold.")
            median_pix = self.log_min
            std_pix = 0.0
            new_mid = self.log_min
            self.min = self.log_min
            self.max = self.log_min
        else:
            median_pix = np.median(vals_masked_flat)
            std_pix = np.std(vals_masked_flat)
            new_mid = np.percentile(vals_masked_flat, self.mid_percentile)
            self.min = vals_masked_flat.min()
            self.max = vals_masked_flat.max()

            new_lower = (median_pix +
                         self.sigma_buffer *
                         std_pix)

            self.lower.add(new_lower)
            self.mid.add(new_mid)
            LOG.info("new_lower: {}".format(new_lower))

        LOG.info("median_pix: {}".format(median_pix))
        LOG.info("std_pix: {}".format(std_pix))
        LOG.info("new_mid: {}".format(new_mid))
        LOG.info("self.min: {}".format(self.min))
        LOG.info("self.max: {}".format(self.max))

    def fit_sigmoid(self):
        # given sampling points on corresponding x and y values,
        # we want to make x as close to the inverse of y as possible
        # using a second order polynomial fit
        mid = max(self.mid(), self.lower() + self.min_mid_buffer)
        x = [self.lower(), mid, mid + self.upper_buffer]
        sigmoid_y = np.array([self.lower_out, 0.5, self.upper_out])
        y = self.inv_tanh_sigmoid(sigmoid_y)

        self.poly_coefficients = np.polyfit(x, y, 2)
        self.check_monotonic()

    def check_monotonic(self):
        first_dir = np.polyder(self.poly_coefficients, 1)
        slope_at_min = np.polyval(first_dir, self.min)
        slope_at_max = np.polyval(first_dir, self.max)
        if slope_at_min <= 0 or slope_at_max <= 0:
            LOG.warning('Sigmoid fit is not monotonically increasing.')

    def adjusted_sigmoid(self, vals):
        y = np.polyval(self.poly_coefficients, vals)
        return self.tanh_sigmoid(y)

    def tanh_sigmoid(self, vals):
        return((np.tanh(vals)+1)/2)

    def inv_tanh_sigmoid(self, vals):
        return(np.arctanh(2*vals-1))


class MovingAverage(object):
    def __init__(self, length):
        self.length = length
        self.history = deque(maxlen=length)
        self.cumsum = 0.0

    def __call__(self):
        return self.cumsum / len(self.history)

    def add(self, value):
        if len(self.history) >= self.length:
            self.cumsum -= self.history.popleft()
        self.history.append(value)
        self.cumsum += value

    def is_valid(self):
        return len(self.history)
