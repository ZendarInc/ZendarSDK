import numpy as np

from util import vec3d_to_array
from radar_data_streamer import RadarData


class RadarPointCloud(RadarData):
    def __init__(self, timestamp, frame_id,
                 point_cloud_local, point_cloud_ecef):
        self.timestamp = timestamp
        self.frame_id = frame_id
        self.point_cloud_local = point_cloud_local
        self.point_cloud_ecef = point_cloud_ecef

    @classmethod
    def from_proto(cls, tracker_state_pb):
        time_record = tracker_state_pb.timestamp
        frame_id = tracker_state_pb.frame_id

        point_cloud_local = []
        point_cloud_ecef = []
        for pt in tracker_state_pb.detection:
            xyz = polar2cartesian(pt.range,
                                  pt.azimuth,
                                  pt.elevation)

            if xyz is not None:
                point_cloud_local.append(xyz)

            ecef = vec3d_to_array(pt.position)
            if np.isnan(ecef[0]) or np.isnan(ecef[1]) or np.isnan(ecef[2]):
                continue

            point_cloud_ecef.append(ecef)

        radar_point_cloud = cls(time_record.common, frame_id,
                                point_cloud_local, point_cloud_ecef)

        return radar_point_cloud


def polar2cartesian(r, azimuth, elevation):
    x = r*np.cos(elevation)*np.cos(azimuth)
    y = r*np.cos(elevation)*np.sin(azimuth)
    z = r*np.sin(elevation)

    #TODO::need to figure out why some are NaN
    if np.isnan(x) or np.isnan(y) or np.isnan(z):
        return None

    xyz = np.array([x, y, z])
    return xyz
