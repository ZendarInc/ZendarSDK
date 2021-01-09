import numpy as np

from util import vec3d_to_array
from radar_data_streamer import RadarData


class LidarPoint(object):
    def __init__(self, position, intensity):
        self.position = position
        self.intensity = intensity

    @classmethod
    def from_proto(cls, lidar_pb):


        point = cls(np.array(lidar_pb.position.x,
                             lidar_pb.position.y,
                             lidar_pb.position.z),
                    lidar_pb.intensity)
        return point


class LidarPointCloud(RadarData):
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
                point_cloud.append(radar_point)

        radar_point_cloud = cls(time_record.common, frame_id,
                                point_cloud)

        return radar_point_cloud
