import numpy as np

from util import vec3d_to_array
from radar_data_streamer import RadarData


class RadarPoint(object):
    def __init__(self, local_xyz, ecef, range_velocity):
        self.local_xyz = local_xyz
        self.ecef = ecef
        self.range_velocity = range_velocity

    @classmethod
    def from_proto(cls, point_pb):
        xyz = polar2cartesian(point_pb.range,
                              point_pb.azimuth,
                              point_pb.elevation)
        if xyz is None:
            return None

        ecef = vec3d_to_array(point_pb.position)
        if np.isnan(ecef[0]) or np.isnan(ecef[1]) or np.isnan(ecef[2]):
            return None

        point = cls(xyz, ecef, point_pb.range_velocity)
        return point


class RadarPointCloud(RadarData):
    def __init__(self, timestamp, frame_id, point_cloud):
        self.timestamp = timestamp
        self.frame_id = frame_id
        self.point_cloud = point_cloud

    @classmethod
    def from_proto(cls, tracker_state_pb):
        time_record = tracker_state_pb.timestamp
        frame_id = tracker_state_pb.frame_id

        point_cloud = []
        for pt in tracker_state_pb.detection:
            radar_point = RadarPoint.from_proto(pt)
            if radar_point is not None:
                point_cloud.append(radar_point)

        radar_point_cloud = cls(time_record.common, frame_id,
                                point_cloud)

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
