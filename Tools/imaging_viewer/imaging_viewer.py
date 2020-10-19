from os.path import join, exists
from contextlib import ExitStack
import argparse
import numpy as np
from collections import namedtuple
from matplotlib import pyplot as plt
from google.protobuf.text_format import Merge

import data_pb2
from radar_image import RadarImage
from radar_data_streamer import RadarDataStreamer
from radar_image_stream_display import RadarImageStreamDisplay
from radar_image_overlay import (
    draw_timestamp,
    draw_grid_line,
)
from video_writer import VideoWriter


IOPath = namedtuple('IOPath', ['image_pbs_path',
                               'pc_pbs_path',
                               'output_path'])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i',
                        '--input-dir',
                        type=str,
                        help="dataset base directory",
                        required=True)
    parser.add_argument('-o',
                        '--output-dir',
                        type=str,
                        help="output video directory",
                        default=None)
    parser.add_argument('--radar-name',
                        action='append',
                        help="output video with specified radar serial number",
                        required=True)
    parser.add_argument('--frame-rate',
                        type=int,
                        help="output video frame rate",
                        default=10)
    parser.add_argument('--quality-factor',
                        type=int,
                        help="video compression quality factor",
                        default=23)
    args = parser.parse_args()

    fig = plt.figure()
    fig.show()
    artist = None

    input_output_paths = []
    for radar_name in args.radar_name:
        output_path = None
        if args.output_dir is not None:
            output_path = join(args.output_dir, radar_name+".mp4")

        io_path = IOPath(
            image_pbs_path = join(args.input_dir, radar_name+".pbs"),
            pc_pbs_path = join(args.input_dir, radar_name+"_points.pbs"),
            output_path = output_path)

        input_output_paths.append(io_path)

    # create all videos
    for io_path in input_output_paths:
        image_streamer = None
        pc_streamer = None
        video_writer = None

        if exists(io_path.image_pbs_path):
            image_streamer = convert_single_video_stream(
                io_path.image_pbs_path)

        if exists(io_path.pc_pbs_path):
            pc_streamer = convert_point_cloud_stream(io_path.pc_pbs_path)

        with ExitStack() as stack:
            for radar_image, im_rgb in image_streamer:
                (im_height, im_width, _) = im_rgb.shape
                im_rgb = overlay_metadata(radar_image, im_rgb)

                # setup onscreen display
                if artist is None:
                    artist = fig.gca().imshow(
                        np.zeros(im_rgb.shape, dtype=np.uint8))

                # setup video writer
                if args.output_dir is not None and video_writer is None:
                    video_writer = VideoWriter(io_path.output_path,
                                               im_width, im_height,
                                               args.frame_rate,
                                               args.quality_factor)

                    video_writer = stack.enter_context(video_writer)

                # write out frame
                if video_writer is not None:
                    video_writer(im_rgb)

                # on screen display
                artist.set_data(im_rgb)
                fig.canvas.draw()
                plt.pause(1e-4)


def convert_single_video_stream(image_pbs_path):
    """
    convert one radar image pbs file to RGB stream
    """
    radar_image_display = RadarImageStreamDisplay()

    with ExitStack() as stack:
        radar_data_streamer = stack.enter_context(
            RadarDataStreamer(image_pbs_path, data_pb2.Image, RadarImage))

        for radar_image in radar_data_streamer:
            im_rgb = radar_image_display(radar_image.image)

            yield radar_image, im_rgb


def overlay_metadata(radar_image, im_rgb, show_range_marker=False):
    # overlay range markers
    if show_range_marker:
        radar_position = radar_image.extrinsic.position
        center = radar_image.image_model.global_to_image(radar_position)
        pixels_per_meter = 1 / np.linalg.norm(radar_image.image_model.di)
        im_rgb = draw_grid_line(im_rgb,
                                center,
                                pixels_per_meter,
                                separation=5)

    # overlay timestamp
    timestamp = "%2.2f" % radar_image.timestamp
    frame_id = str(radar_image.frame_id)
    im_rgb = draw_timestamp(im_rgb, frame_id + ":" + timestamp)

    return im_rgb


def read_proto_text(path, model):
    """
    read protobuf in text form
    """
    with open(path, 'r') as fp:
        Merge(fp.read(), model)

    return model


if __name__ == "__main__":
    main()
