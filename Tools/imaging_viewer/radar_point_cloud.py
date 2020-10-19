import numpy as np

from util import vec3d_to_array
from radar_data_streamer import RadarData


class RadarPointCloud(RadarData):
    def __init__(self, timestamp, frame_id, point_cloud):
        self.timestamp = timestamp
        self.frame_id = frame_id
        self.point_cloud = point_cloud

    @classmethod
    def from_proto(cls, tracker_state_pb):
        time_record = tracker_state_pb.timestamp
        frame_id = tracker_state_pb.frame_id

        # TODO:: some field from Point field are being ignored here
        point_cloud = []
        for pt in tracker_state_pb.detection:
            xyz = polar2cartesian(pt.range,
                                  pt.azimuth,
                                  pt.elevation)

            point_cloud.append(xyz)

        radar_point_cloud = cls(time_record.common, frame_id, point_cloud)

        return radar_point_cloud


def polar2cartesian(r, azimuth, elevation):
    x = r*np.cos(elevation)*np.cos(azimuth)
    y = r*np.cos(elevation)*np.sin(azimuth)
    z = r*np.sin(elevation)

    xyz = np.array([x, y, z])
    return xyz
