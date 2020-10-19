import numpy as np


def vec3d_to_array(vec):
    return np.array([vec.x, vec.y, vec.z])


def quat_to_array(quat):
    return np.array([quat.w, quat.x, quat.y, quat.z])
