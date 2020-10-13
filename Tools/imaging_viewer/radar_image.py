import numpy as np
from collections import namedtuple

Extrinsic = namedtuple('Extrinsic', ['position', 'attitude'])


class ImageModel(object):

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


class RadarImage(object):
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

    @classmethod
    def to_vehicle_frame(radar_images):
        """
        Take a set of radar images in radar frame and convert all to
        vehicle frame
        """
        pass


def vec3d_to_array(vec):
    return np.array([vec.x, vec.y, vec.z])


def quat_to_array(quat):
    return np.array([quat.w, quat.x, quat.y, quat.z])
