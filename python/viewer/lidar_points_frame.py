import numpy as np

from util import vec3d_to_array
from radar_data_streamer import RadarData


class LidarPoint(object):
    def __init__(self, position_local, position_global, intensity):
        self.position_local = position_local
        self.position_global = position_global
        self.intensity = intensity

    @classmethod
    def from_proto(cls, lidar_pb):
        point = cls(np.array((lidar_pb.position_local.x,
                              lidar_pb.position_local.y,
                              lidar_pb.position_local.z)),
                    np.array((lidar_pb.position_global.x,
                              lidar_pb.position_global.y,
                              lidar_pb.position_global.z)),
                    lidar_pb.intensity)
        return point


class LidarPointsFrame(RadarData):
    def __init__(self, timestamp, point_cloud):
        self.timestamp = timestamp
        self.point_cloud = point_cloud

    @classmethod
    def from_proto(cls, lidar_points_pb):
        time_record = lidar_points_pb.timestamp

        point_cloud = []
        for pt in lidar_points_pb.point_cloud:
            lidar_point = LidarPoint.from_proto(pt)
            if lidar_point is not None:
                point_cloud.append(lidar_point)

        lidar_point_frame = cls(time_record, point_cloud)

        return lidar_point_frame
