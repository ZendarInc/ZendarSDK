from os.path import join, exists
import sys
from contextlib import ExitStack
import argparse
import numpy as np
from collections import namedtuple
from matplotlib import pyplot as plt
import cv2

import data_pb2
from radar_image import RadarImage
from radar_point_cloud import RadarPointCloud
from radar_data_streamer import RadarDataStreamer
from radar_image_stream_display import RadarImageStreamDisplay
from radar_image_overlay import draw_timestamp
from video_writer import VideoWriter


IOPath = namedtuple('IOPath', ['image_pbs_path',
                               'pc_pbs_path',
                               'output_path'])

ImagePcPair = namedtuple('ImagePcPair', ['image',
                                         'pc'])

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
            image_pbs_path = join(args.input_dir, radar_name+"_images.pbs"),
            pc_pbs_path = join(args.input_dir, radar_name+"_points.pbs"),
            output_path = output_path)

        input_output_paths.append(io_path)

    # create all videos
    for io_path in input_output_paths:
        video_writer = None

        with ExitStack() as stack:
            for image_pc_pair in sync_streams(io_path.image_pbs_path,
                                              io_path.pc_pbs_path):
                if image_pc_pair.image is None and image_pc_pair.pc is None:
                    break

                # create rgb image from point cloud / SAR
                im_rgb = to_rgb_image(image_pc_pair)
                (im_height, im_width, _) = im_rgb.shape

                # get timestamp and frame id
                if image_pc_pair.pc is not None:
                    timestamp = image_pc_pair.pc.timestamp
                    frame_id = image_pc_pair.pc.frame_id
                else:
                    timestamp = image_pc_pair.image.timestamp
                    frame_id = image_pc_pair.image.frame_id

                im_rgb = overlay_timestamp(timestamp, frame_id, im_rgb)

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


def sync_streams(image_pbs_path, pc_pbs_path):
    """
    this function synchronizes the image and point cloud stream
    """
    radar_image_streamer = None
    point_cloud_streamer = None

    with ExitStack() as stack:
        if image_pbs_path is not None:
            radar_image_streamer = stack.enter_context(
                RadarDataStreamer(image_pbs_path,
                                  data_pb2.Image,
                                  RadarImage))

        if pc_pbs_path is not None:
            point_cloud_streamer = stack.enter_context(
                RadarDataStreamer(pc_pbs_path,
                                  data_pb2.TrackerState,
                                  RadarPointCloud))

        if radar_image_streamer is not None and point_cloud_streamer is not None:
            radar_image_streamer = iter(radar_image_streamer)
            point_cloud_streamer = iter(point_cloud_streamer)

            radar_image = next(radar_image_streamer)
            pc = next(point_cloud_streamer)

            # sync the two streams at the head
            while radar_image.timestamp - pc.timestamp > 0.1:
                pc = next(point_cloud_streamer)
                continue

            while pc.timestamp - radar_image.timestamp > 0.1:
                radar_image = next(radar_image_streamer)
                continue

            # display only the overlaid section
            while True:
                try:
                    radar_image = next(radar_image_streamer)
                except StopIteration:
                    yield ImagePcPair(image=None, pc=None)

                while pc.timestamp - radar_image.timestamp <= 0.1:
                    yield ImagePcPair(image=radar_image, pc=pc)

                    try:
                        pc = next(point_cloud_streamer)
                    except StopIteration:
                        yield ImagePcPair(image=None, pc=None)

        elif radar_image_streamer is not None:
            for radar_image in radar_image_streamer:
                yield ImagePcPair(image=radar_image, pc=None)

        elif point_cloud_streamer is not None:
            for point_cloud in point_cloud_streamer:
                yield ImagePcPair(image=None, pc=point_cloud)

        else:
            sys.exit("No point cloud or image stream file")


def to_rgb_image(image_pc_pair):
    """
    convert raw sar image and / or point cloud into 8-bit RGB for display
    """
    im_rgb = None
    radar_image_display = RadarImageStreamDisplay()

    if image_pc_pair.image is not None:
        im_rgb = radar_image_display(image_pc_pair.image.image)

    if image_pc_pair.pc is not None:
        if im_rgb is not None:
            for pt in image_pc_pair.pc.point_cloud_ecef:
                # use the image model to project ecef points to sar
                y, x = image_pc_pair.image.image_model.global_to_image(pt)
                cv2.circle(im_rgb,
                           center=(int(y), int(x)),
                           radius=1,
                           color=(102, 178, 255),
                           thickness=-1)

        else:
            # create default image region
            xmin = 0
            xmax = 60
            ymin = -30
            ymax = 30
            im_res = 0.1

            imsize_y = int((ymax - ymin) / im_res)
            imsize_x = int((xmax - xmin) / im_res)

            im_rgb = np.zeros((imsize_y, imsize_x, 3), dtype=np.uint8)

            pts = np.copy(image_pc_pair.pc.point_cloud_local)
            if len(pts) == 0:
                return im_rgb

            im_pts = np.array(pts)
            im_pts[:,0] = (im_pts[:,0] - xmin) / im_res
            im_pts[:,1] = (im_pts[:,1] - ymin) / im_res

            for (x, y, _) in im_pts:
                cv2.circle(im_rgb,
                           center=(int(y), int(x)),
                           radius=1,
                           color=(102, 178, 255),
                           thickness=-1)

    return im_rgb


def overlay_timestamp(timestamp, frame_id, im_rgb):
    timestamp = "%2.2f" % timestamp
    frame_id = "%d" % frame_id
    im_rgb = draw_timestamp(im_rgb, frame_id + ":" + timestamp)

    return im_rgb


if __name__ == "__main__":
    main()
