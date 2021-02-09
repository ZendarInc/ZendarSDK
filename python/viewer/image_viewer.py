from os.path import join, exists
import sys
from contextlib import ExitStack
import argparse
import numpy as np
from collections import namedtuple
from matplotlib import pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
import cv2

import data_pb2
from radar_image import (
    RadarImage,
)
from radar_data_streamer import (
    ProtoStreamReader,
    ProtoStreamWriter,
)
from lidar_points_frame import LidarPointsFrame
from radar_point_cloud import RadarPointCloud
from radar_image_stream_display import RadarImageStreamDisplay
from radar_image_overlay import draw_timestamp
from video_writer import VideoWriter


IOPath = namedtuple('IOPath', ['image_pbs_path',
                               'pc_pbs_path',
                               'lidar_pbs_path',
                               'video_output_path',
                               'image_model_output_path'])

RenderData = namedtuple('RenderData', ['image',
                                       'pc',
                                       'lidar'])


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
                        help="generate video with specific radar serial (left radar first).",
                        required=True)
    parser.add_argument('--frame-rate',
                        type=int,
                        help="output video frame rate",
                        default=10)
    parser.add_argument('--quality-factor',
                        type=int,
                        help="video compression quality factor",
                        default=25)
    parser.add_argument('--show-timestamp',
                        action='store_true')
    parser.add_argument('--no-sar',
                        action='store_true')
    parser.add_argument('--no-point-cloud',
                        action='store_true')
    parser.add_argument('--lidar',
                        action='store_true')
    parser.add_argument('--color-by-elevation',
                        action='store_true')

    args = parser.parse_args()

    fig = plt.figure()
    fig.show()
    artist = None

    input_output_paths = []
    if (not args.no_sar) or (not args.no_point_cloud):
        assert(args.radar_name is not None), \
                "Radar name is required except for lidar-only"
    if args.radar_name is None:
        io_path = get_io_paths('', args.input_dir, args.output_dir,
                               no_sar=args.no_sar,
                               no_point_cloud=args.no_point_cloud,
                               lidar=args.lidar)
        input_output_paths.append(io_path)
    else:
        for radar_name in args.radar_name:
            io_path = get_io_paths(radar_name, args.input_dir, args.output_dir,
                                   no_sar=args.no_sar,
                                   no_point_cloud=args.no_point_cloud,
                                   lidar=args.lidar)
            input_output_paths.append(io_path)

    # create individual outputs
    for io_path in input_output_paths:
        video_writer = None

        last_frame_id = 0
        with ExitStack() as stack:
            for render_data in sync_streams(io_path.image_pbs_path,
                                              io_path.pc_pbs_path,
                                              io_path.lidar_pbs_path):
                if render_data.image is None \
                   and render_data.pc is None \
                   and render_data.lidar is None:
                    break

                # create rgb image from point cloud / SAR
                im_rgb = to_rgb_image(render_data, args.color_by_elevation)

                # flip image because image (0,0) is at top left corner
                # while radar image (0,0) is at bottom left corner
                im_rgb = np.copy(np.flip(im_rgb, axis=0))
                (im_height, im_width, _) = im_rgb.shape

                # get timestamp and frame id
                if render_data.pc is not None:
                    timestamp = render_data.pc.timestamp
                    frame_id = render_data.pc.frame_id
                elif render_data.image is not None:
                    timestamp = render_data.image.timestamp
                    frame_id = render_data.image.frame_id
                else:
                    # Lidar-only doesn't use the frame_id
                    timestamp = render_data.lidar.timestamp
                    frame_id = 0

                if frame_id - last_frame_id > 1 and frame_id > 0:
                    print("DROP FRAME DETECTED: %d" % frame_id)
                last_frame_id = frame_id

                if args.show_timestamp:
                    im_rgb = overlay_timestamp(timestamp, frame_id, im_rgb)

                # setup onscreen display
                if artist is None:
                    artist = fig.gca().imshow(
                        np.zeros(im_rgb.shape, dtype=np.uint8))

                # setup video writer and image model writer
                if args.output_dir is not None and video_writer is None:
                    video_writer = VideoWriter(io_path.video_output_path,
                                               im_width, im_height,
                                               args.frame_rate,
                                               args.quality_factor)
                    video_writer = stack.enter_context(video_writer)

                    proto_writer = stack.enter_context(
                        ProtoStreamWriter(io_path.image_model_output_path))

                # write out frame
                if video_writer is not None:
                    video_writer(im_rgb)

                    if render_data.image is not None:
                        proto_out = render_data.image.to_proto(timestamp,
                                                                 frame_id)
                        proto_writer.write(proto_out)

                # on screen display
                artist.set_data(im_rgb)
                fig.canvas.draw()
                plt.pause(1e-4)

    # This is not the greatest way to merge videos from multiple cameras.
    # For visualization is this okey
    if len(input_output_paths) != 2:
        return

    left_video = cv2.VideoCapture(input_output_paths[0].video_output_path)
    right_video = cv2.VideoCapture(input_output_paths[1].video_output_path)
    merged_video_path = join(args.output_dir, "merged_video.mp4")
    merged_video_writer = None

    print("merging video ...")
    frame_count = 0
    with ExitStack() as stack:
        while left_video.isOpened() and right_video.isOpened():
            _, left_frame = left_video.read()
            _, right_frame = right_video.read()

            combined_frame = np.vstack((left_frame, right_frame))
            combined_frame = cv2.cvtColor(combined_frame, cv2.COLOR_BGR2RGB)
            combined_frame = cv2.rotate(combined_frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

            if merged_video_writer is None:
                (im_height, im_width, _) = combined_frame.shape
                merged_video_writer = VideoWriter(merged_video_path,
                                                  im_width, im_height,
                                                  args.frame_rate,
                                                  args.quality_factor)
                merged_video_writer = stack.enter_context(merged_video_writer)

            merged_video_writer(combined_frame)
            frame_count += 1

            if frame_count % 100 == 0:
                print("wrote %s frames" % frame_count)


def sync_streams(image_pbs_path, pc_pbs_path, lidar_pbs_path):
    """
    this function synchronizes the image, point cloud, and lidar streams
    """
    radar_image_streamer = None
    point_cloud_streamer = None
    lidar_cloud_streamer = None

    with ExitStack() as stack:
        if image_pbs_path is not None:
            radar_image_streamer = stack.enter_context(
                ProtoStreamReader(image_pbs_path,
                                  data_pb2.Image,
                                  RadarImage))

        if pc_pbs_path is not None:
            point_cloud_streamer = stack.enter_context(
                ProtoStreamReader(pc_pbs_path,
                                  data_pb2.TrackerState,
                                  RadarPointCloud))

        if lidar_pbs_path is not None:
            lidar_cloud_streamer = stack.enter_context(
                ProtoStreamReader(lidar_pbs_path,
                                  data_pb2.LidarPointsFrame,
                                  LidarPointsFrame))
        streams = {}
        data = {}
        if radar_image_streamer is not None:
            streams['radar'] = iter(radar_image_streamer)
        if point_cloud_streamer is not None:
            streams['pc'] = iter(point_cloud_streamer)
        if lidar_cloud_streamer is not None:
            streams['lidar'] = iter(lidar_cloud_streamer)

        for key in streams:
            data[key] = next(streams[key])
        # Synchronize the streams once at the start
        while True:
            # Check if data streams are synced
            max_timestamp = 0
            for values in data.values():
                if values.timestamp > max_timestamp:
                    max_timestamp = values.timestamp
            synchronized = True
            for values in data.values():
                if max_timestamp - values.timestamp > 0.1:
                    synchronized = False
            if synchronized:
                break
            # Iterate each stream until its timestamp is either close to or
            # later than the latest timestamp
            for key in streams:
                while max_timestamp - data[key].timestamp > 0.1:
                    data[key] = next(streams[key])

        # display only the overlaid section
        while True:
            for key in streams:
                try:
                    data[key] = next(streams[key])
                except StopIteration:
                    yield RenderData(image=None, pc=None, lidar=None)
                if data[key].timestamp > max_timestamp:
                    max_timestamp = data[key].timestamp

            image = data['radar'] if 'radar' in streams else None
            pc    = data['pc']    if 'pc'    in streams else None
            lidar = data['lidar'] if 'lidar' in streams else None
            yield RenderData(image=image, pc=pc, lidar=lidar)

            # Catch up to the most ahead timestamp with the other streams
            for key in streams:
                while max_timestamp - data[key].timestamp > 0.1:
                    try:
                        data[key] = next(streams[key])
                    except StopIteration:
                        yield RenderData(image=None, pc=None, lidar=None)
                    image = data['radar'] if 'radar' in streams else None
                    pc    = data['pc']    if 'pc'    in streams else None
                    lidar = data['lidar'] if 'lidar' in streams else None
                    yield RenderData(image=image, pc=pc, lidar=lidar)


MAX_DOPPLER = 20
cmap_doppler = ScalarMappable(norm=Normalize(vmin=-MAX_DOPPLER,
                                             vmax=MAX_DOPPLER),
                              cmap=plt.get_cmap('RdYlGn'))

MAX_ELEVATION = 7
cmap_elevation = ScalarMappable(norm=Normalize(vmin=-MAX_ELEVATION,
                                               vmax=MAX_ELEVATION),
                                cmap=plt.get_cmap('PuOr'))


def to_rgb_image(render_data, color_by_elevation=False):
    """
    convert raw sar image and / or point cloud into 8-bit RGB for display
    """
    im_rgb = None
    radar_image_display = RadarImageStreamDisplay()

    # Default image region
    xmin = 0
    xmax = 60
    ymin = -30
    ymax = 30
    im_res = 0.1
    imsize_y = int((ymax - ymin) / im_res)
    imsize_x = int((xmax - xmin) / im_res)

    if render_data.image is not None:
        im_rgb = radar_image_display(render_data.image.image)
    else:
        im_rgb = np.zeros((imsize_x, imsize_y, 3), dtype=np.uint8)
    if render_data.pc is not None:
        if render_data.image is not None:
            for pt in render_data.pc.point_cloud:
                # use the image model to project ecef points to sar
                x, y = render_data.image.image_model.global_to_image(pt.ecef)
                if color_by_elevation:
                    color = cmap_elevation.to_rgba(pt.local_xyz[2])
                else:
                    color = cmap_doppler.to_rgba(pt.range_velocity)
                draw_tracker_point(im_rgb, x, y, color)
        else:
            for pt in render_data.pc.point_cloud:
                im_pt_x = (pt.local_xyz[1] - xmin) / im_res
                im_pt_y = (pt.local_xyz[0] - ymin) / im_res
                if color_by_elevation:
                    color = cmap_elevation.to_rgba(pt.local_xyz[2])
                else:
                    color = cmap_doppler.to_rgba(pt.range_velocity)
                draw_tracker_point(im_rgb, im_pt_x, im_pt_y, color)
    if render_data.lidar is not None:
        if render_data.image is not None:
            for pt in render_data.lidar.point_cloud:
                # use the image model to project ecef points to sar
                x, y = render_data.image.image_model.global_to_image(
                    pt.position_global)
                draw_lidar_point(im_rgb, x, y)
        else:
            for pt in render_data.lidar.point_cloud:
                im_pt_x = (pt.position_local[1] - xmin) / im_res
                im_pt_y = (-pt.position_local[0] - ymin) / im_res
                draw_lidar_point(im_rgb, im_pt_x, im_pt_y)

    return im_rgb


def overlay_timestamp(timestamp, frame_id, im_rgb):
    timestamp = "%2.2f" % timestamp
    frame_id = "%d" % frame_id
    im_rgb = draw_timestamp(im_rgb, frame_id + ":" + timestamp)

    return im_rgb


def draw_tracker_point(im, x, y, c):
    r = int(255*c[0])
    g = int(255*c[1])
    b = int(255*c[2])

    cv2.circle(im,
               center=(int(x), int(y)),
               radius=1,
               color=(r, g, b),
               thickness=-1)

def draw_lidar_point(im, x, y):
    cv2.circle(im,
               center=(int(x), int(y)),
               radius=1,
               color=(135, 206, 250),
               thickness=-1)

def get_io_paths(radar_name, input_dir, output_dir,
                 no_sar=False, no_point_cloud=False, lidar=False):
    image_pbs_path = None
    pc_pbs_path = None
    lidar_pbs_path = None
    video_output_path = None
    image_model_output_path = None

    if no_sar:
        print("radar image display is turned off")
    else:
        image_pbs_path = join(input_dir, radar_name + "_images.pbs")

        if not exists(image_pbs_path):
            image_pbs_path = None
            print("radar image at [%s] is not found" % image_pbs_path)

    if no_point_cloud:
        print("radar point cloud display is turned off")
    else:
        pc_pbs_path = join(input_dir, radar_name + "_points.pbs")
        if not exists(pc_pbs_path):
            pc_pbs_path = None
            print("radar point cloud at [%s] is not found" % pc_pbs_path)

    if not lidar:
        print("lidar display is turned off")
    else:
        lidar_pbs_path = join(input_dir, "lidar.pbs")
        assert exists(lidar_pbs_path), \
            "lidar point cloud at [%s] is not found" % pc_pbs_path

    if output_dir is not None:
        video_output_path = join(output_dir, radar_name + ".mp4")
        image_model_output_path = join(output_dir, radar_name + "_image_models.pbs")

    io_path = IOPath(
        image_pbs_path=image_pbs_path,
        pc_pbs_path=pc_pbs_path,
        lidar_pbs_path=lidar_pbs_path,
        video_output_path=video_output_path,
        image_model_output_path=image_model_output_path)

    return io_path


if __name__ == "__main__":
    main()
