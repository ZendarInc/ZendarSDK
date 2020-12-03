import numpy as np
from collections import namedtuple
from util import (
    vec3d_to_array,
    quat_to_array,
)
from radar_data_streamer import RadarData
from data_pb2 import Image

Extrinsic = namedtuple('Extrinsic', ['position', 'attitude'])


class RadarImage(RadarData):
    """
    This class is a Python representation of the protobuf Image object for
    convinent downstream operations
    """
    def __init__(self, timestamp, frame_id, extrinsic, image_model, image):
        self.timestamp = timestamp
        self.frame_id = frame_id
        self.extrinsic = extrinsic
        self.image_model = image_model
        self.image = image

    @classmethod
    def from_proto(cls, image_pb):
        timestamp = image_pb.timestamp
        frame_id = image_pb.frame_id

        extrinsic = Extrinsic(
            position=vec3d_to_array(image_pb.position),
            attitude=quat_to_array(image_pb.attitude))

        image_model = ImageModel(
            origin=vec3d_to_array(image_pb.cartesian.model.origin),
            di=vec3d_to_array(image_pb.cartesian.model.di),
            dj=vec3d_to_array(image_pb.cartesian.model.dj))

        # create the image array
        image_shape = (image_pb.cartesian.data.cols,
                       image_pb.cartesian.data.rows)

        image_data = np.frombuffer(image_pb.cartesian.data.data,
                                   dtype=np.uint32)

        # copy image_data because we do not own the memory
        image = np.reshape(image_data.copy(), image_shape)

        radar_image = cls(timestamp, frame_id, extrinsic, image_model, image)

        return radar_image

    def to_proto(self, timestamp, frame_id):
        image_pb = Image()

        image_pb.timestamp = timestamp
        image_pb.frame_id = frame_id
        image_pb.position.x = self.extrinsic.position[0]
        image_pb.position.y = self.extrinsic.position[1]
        image_pb.position.z = self.extrinsic.position[2]

        image_pb.attitude.w = self.extrinsic.attitude[0]
        image_pb.attitude.x = self.extrinsic.attitude[1]
        image_pb.attitude.y = self.extrinsic.attitude[2]
        image_pb.attitude.z = self.extrinsic.attitude[3]

        image_pb.cartesian.model.origin.x = self.image_model.origin[0]
        image_pb.cartesian.model.origin.y = self.image_model.origin[1]
        image_pb.cartesian.model.origin.z = self.image_model.origin[2]

        image_pb.cartesian.model.di.x = self.image_model.di[0]
        image_pb.cartesian.model.di.y = self.image_model.di[1]
        image_pb.cartesian.model.di.z = self.image_model.di[2]

        image_pb.cartesian.model.dj.x = self.image_model.dj[0]
        image_pb.cartesian.model.dj.y = self.image_model.dj[1]
        image_pb.cartesian.model.dj.z = self.image_model.dj[2]

        image_pb.cartesian.data.cols = self.image.shape[0]
        image_pb.cartesian.data.rows = self.image.shape[1]

        return image_pb


class ImageModel(object):
    """
    ImageModel describing mapping from world coordinate to image model
    """
    def __init__(self, origin, di, dj):
        self.di = di
        self.dj = dj
        self.origin = origin

    def global_to_image(self, ecef_point):
        radar_to_image = ecef_point - self.origin
        i_res = np.linalg.norm(self.di)
        j_res = np.linalg.norm(self.dj)
        i_dir = self.di/i_res
        j_dir = self.dj/j_res
        i_proj = int(round(radar_to_image.dot(i_dir)/i_res))
        j_proj = int(round(radar_to_image.dot(j_dir)/j_res))
        pixel_point = (i_proj, j_proj)

        return pixel_point

    def image_to_global(self, pixel_point):
        i_idx = pixel_point[0]
        j_idx = pixel_point[1]
        ecef_point = self.origin + (i_idx*self.di) + (j_idx*self.dj)

        return ecef_point
