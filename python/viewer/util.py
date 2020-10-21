import numpy as np
from google.protobuf.text_format import Merge


def vec3d_to_array(vec):
    return np.array([vec.x, vec.y, vec.z])


def quat_to_array(quat):
    return np.array([quat.w, quat.x, quat.y, quat.z])


def read_proto_text(path, model):
    """
    read protobuf in text form
    """
    with open(path, 'r') as fp:
        Merge(fp.read(), model)

    return model
