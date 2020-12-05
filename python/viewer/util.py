import numpy as np
from google.protobuf.text_format import Merge


def vec3d_to_array(vec):
    return np.array([vec.x, vec.y, vec.z])


def quat_to_array(quat):
    return np.array([quat.w, quat.x, quat.y, quat.z])


def array_to_vec3d_pb(vec_pb, input_array):
    vec_pb.x, vec_pb.y, vec_pb.z = input_array
    return vec_pb


def array_to_quat_pb(quat_pb, input_array):
    quat_pb.w, quat_pb.x, quat_pb.y, quat_pb.z = input_array
    return quat_pb


def read_proto_text(path, model):
    """
    read protobuf in text form
    """
    with open(path, 'r') as fp:
        Merge(fp.read(), model)

    return model
