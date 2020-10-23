import math
from cv2 import (
    putText,
    circle,
    FONT_HERSHEY_DUPLEX,
)


def draw_grid_line(im_rgb, center, pixels_per_meter, separation=10):
    nrows = im_rgb.shape[0]
    ncols = im_rgb.shape[1]
    pixels_per_meter = int(math.ceil(pixels_per_meter))
    assert pixels_per_meter > 0

    radius = separation*pixels_per_meter
    while (radius < max(ncols, nrows)):
        circle(im_rgb, center, radius, (255, 255, 255), 2)
        radius = radius + separation*pixels_per_meter
    return im_rgb


def draw_timestamp(im_rgb, text):
    im_rows = im_rgb.shape[0]
    im_cols = im_rgb.shape[1]

    position = (0, im_rows-20)
    putText(im_rgb,
            text,
            position,
            fontFace=FONT_HERSHEY_DUPLEX,
            fontScale=1.0,
            color=(50, 205, 50),
            thickness=1)
    return im_rgb
