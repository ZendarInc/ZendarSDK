import numpy as np
from collections import namedtuple
from util import (
    vec3d_to_array,
    quat_to_array,
    array_to_vec3d_pb,
    array_to_quat_pb,
)
from radar_data_streamer import RadarData
from data_pb2 import Image

Extrinsic = namedtuple('Extrinsic', ['position', 'attitude'])


class ImageModelCartesian(RadarData):
    def __init__(self, timestamp, dim_u, dim_v, origin, du, dv,
                 u_track_aligned=True, aperture_center=None,
                 track_dir=None, up_dir=None, fc=None):

        """
        dim_u, dim_v: image width and height in pixels.
        origin: image's coordinate origin (top left) in space.
        du: width of a pixel (vector).
        dv: height of a pixel (vector).
        u_track_aligned: whether the u dimension is more closely
        aligned with the track (as is typical in side-facing) or
        cross-track (as is more typical with front-facing)
        track_vector: a vector pointing along the track
        """
        self.timestamp = timestamp

        self.origin = origin
        self.dim_u = dim_u
        self.dim_v = dim_v
        self.du = du
        self.dv = dv
        self.u_track_aligned = u_track_aligned
        
        self.u_res = np.linalg.norm(du)
        self.u_dir = du / self.u_res
        self.v_res = np.linalg.norm(dv)
        self.v_dir = dv / self.v_res
        
        self.aperture_center = aperture_center
        if track_dir is not None:
            self.track_dir = track_dir / np.linalg.norm(track_dir)
        else:
            self.track_dir = None
        if up_dir is not None:
            self.up_dir = up_dir / np.linalg.norm(up_dir)
        else:
            self.up_dir = None
        
        self.fc = fc

    @classmethod
    def from_proto(cls, image_model_pb):
        timestamp = image_model_pb.timestamp_start.common
        dim_u = image_model_pb.image_model.nu
        dim_v = image_model_pb.image_model.nv
        origin = np.array([image_model_pb.image_model.origin.x,
                           image_model_pb.image_model.origin.y,
                           image_model_pb.image_model.origin.z])
        du = np.array([image_model_pb.image_model.dxyz_du.x,
                       image_model_pb.image_model.dxyz_du.y,
                       image_model_pb.image_model.dxyz_du.z])
        dv = np.array([image_model_pb.image_model.dxyz_dv.x,
                       image_model_pb.image_model.dxyz_dv.y,
                       image_model_pb.image_model.dxyz_dv.z])

        if image_model_pb.image_model.HasField('aperture_center'):
            aperture_center = np.array([image_model_pb.image_model.aperture_center.x,
                                        image_model_pb.image_model.aperture_center.y,
                                        image_model_pb.image_model.aperture_center.z])

        return cls(timestamp, dim_u, dim_v, origin, du, dv,
                   aperture_center=aperture_center)

    def global_to_local(self, ecef_point):
        """
        Project a point to the vehicle centric coordinates
        """
        w_dir = np.cross(self.u_dir, self.v_dir)
        shift_vec = ecef_point - self.origin
        return np.array([shift_vec.dot(self.u_dir),
                         shift_vec.dot(self.v_dir),
                         shift_vec.dot(w_dir)])

    def global_to_image(self, ecef_point):
        """
        project a point in global (ECEF) to SAR image
        """
        shift_vec = ecef_point - self.origin
        u_projected = shift_vec.dot(self.u_dir) / self.u_res
        v_projected = shift_vec.dot(self.v_dir) / self.v_res

        image_point = (u_projected, v_projected)

        return image_point

    def image_to_global(self, image_point):
        """
        project a point in SAR image to global (ECEF)
        """
        u = image_point[1]
        v = image_point[0]
        ecef_point = u * self.du + v * self.dv + self.origin

        return ecef_point


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
        # Setting the type to REAL_32U
        image_pb.cartesian.data.type = 5
        array_to_vec3d_pb(image_pb.position,
                          self.extrinsic.position)

        array_to_quat_pb(image_pb.attitude,
                         self.extrinsic.attitude)

        array_to_vec3d_pb(image_pb.cartesian.model.origin,
                          self.image_model.origin)

        array_to_vec3d_pb(image_pb.cartesian.model.di,
                          self.image_model.di)

        array_to_vec3d_pb(image_pb.cartesian.model.dj,
                          self.image_model.dj)

        image_pb.cartesian.data.cols, image_pb.cartesian.data.rows = \
            self.image.shape

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
