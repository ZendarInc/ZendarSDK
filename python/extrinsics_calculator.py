import argparse
import numpy as np

from third_party.transformations import quaternion_from_matrix

"""
This script calculates the rotation of the radar extrinsics given the yaw
angle of the radar. The extrinsic describes the transformation of a point in
the radar coordinate to the vechicle coordinate.

Zendar's vehicle coordinate is
    x = forward
    y = left
    z = up

Zendar's radar coordinate is
    x = left
    y = up
    z = forward

A simple way to achieve this transformation is to take a forward facing radar,
transform it into the vehicle coordinate system and then rotating around it
z-axis.
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i',
                        '--yaw',
                        type=float,
                        help="radar yaw angle in degrees (anti-clockwise direction)",
                        required=True)
    args = parser.parse_args()

    # construction rotation matrix around z-axis
    rad = np.radians(args.yaw)
    rot_z = np.array([[np.cos(rad), -np.sin(rad), 0],
                      [np.sin(rad),  np.cos(rad), 0],
                      [0          ,  0          , 1]])

    # construction left-up-forward to forward-left-up rotation
    rot_as = np.array([[0, 0, 1],
                       [1, 0, 0],
                       [0, 1, 0]])

    # rotation matrix from radar coordinate to vehicle coordinate
    r_radar_veh = np.dot(rot_z, rot_as)
    quat = quaternion_from_matrix(r_radar_veh, isprecise=True)

    print("Rotation (quaternion) of the extrinsic is")
    print("[w = %2.8f]" % quat[0])
    print("[x = %2.8f]" % quat[1])
    print("[y = %2.8f]" % quat[2])
    print("[z = %2.8f]" % quat[3])


if __name__ == "__main__":
    main()
