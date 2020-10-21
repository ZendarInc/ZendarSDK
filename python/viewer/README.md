# Imaging Viewer

Imaging Viewer is an example Python program that converts recorded raw radar images
to human-viewable mp4 video. This program demonstrates how to:

- load recorded data from file
- perform coordinate transform to project two radar views into common vehicle
  coordinate system
- compress the high dynamic range radar image suitable for viewing

## Running the viewer

    $> python3 imaging_viewer.py -i <data dir> -o <output filename.mp4>

for more options, type

    $> python3 imaging_viewer.py --help
