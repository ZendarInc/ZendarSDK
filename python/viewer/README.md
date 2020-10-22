# Image Viewer

Imaging Viewer is an example Python program that converts recorded raw radar images and point detections, overlay the two data types and displays the images. It optionally lets the user to store the images are an mp4 video.

This program demonstrates how to:

- load recorded image and point detections from file
- synchronize the two data streams
- project point detections on to the radar images
- compress the high dynamic range radar image suitable for viewing

## Running the viewer

    $> python3 image_viewer.py
        -i <data dir>
        -o <output filename.mp4>
        --radar-name <left_radar_name, e.g. 1739000J1Q>
        --radar-name <right_radar_name, e.g. 1739000J18>

for more options, type

    $> python3 image_viewer.py --help
