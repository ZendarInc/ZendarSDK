import numpy as np
from matplotlib import pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

from sigmoid import Sigmoid


class RadarImageStreamDisplay(object):
    """
    Display a radar image by applying a nonlinear history-dependent
    intensity compression from 32 bit integer to 8 bit integer
    """
    def __init__(self):
        self.sigmoid = Sigmoid()

    def __call__(self, radar_image_mag):
        """
        image_abs[image_abs < 1] = 1
        im = np.log10(image_abs)
        im = im / np.max(im) # scale between 0 and 1
        """
        im = self.sigmoid(radar_image_mag)
        im_rgb = create_bitmap(im)

        return im_rgb


cmap = ScalarMappable(norm=Normalize(vmin=0, vmax=1),
                      cmap=plt.get_cmap('inferno'))


def create_bitmap(image_abs):
    """
    map a single-channel float image into an three-channel RGB image
    using predefined colormap

    The image has range [0, 1]
    """
    return (cmap.to_rgba(image_abs)[..., :3]*255).astype(np.uint8)
