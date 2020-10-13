import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# This is a "magic" number which is estimated by profiling how many unique
# grid cells the device can process at peak-performance, it is the
# count of the number of cells permitted in a single image.
RESOLUTION_CALIBRATION_SIZE = 25 ** 2
RESOLUTION_CALIBRATION_BASE = 0.04


_EPS = np.finfo(float).eps * 4.0


def quaternion_matrix(quaternion):
    q = np.array(quaternion, dtype=np.float64, copy=True)
    n = np.dot(q, q)
    if n < _EPS:
        return np.identity(3)
    q *= math.sqrt(2.0 / n)
    q = np.outer(q, q)
    return np.array([
        [1.0-q[2, 2]-q[3, 3],     q[1, 2]-q[3, 0],     q[1, 3]+q[2, 0]],
        [    q[1, 2]+q[3, 0], 1.0-q[1, 1]-q[3, 3],     q[2, 3]-q[1, 0]],
        [    q[1, 3]-q[2, 0],     q[2, 3]+q[1, 0], 1.0-q[1, 1]-q[2, 2]]])


def quaternion_about_axis(angle, axis):
    q = np.array([0.0, axis[0], axis[1], axis[2]])
    qlen = np.linalg.norm(q)
    if qlen > _EPS:
        q *= math.sin(angle/2.0) / qlen
    q[0] = math.cos(angle/2.0)
    return q


class Bbox:
    def __init__(self, x0, y0, x1, y1):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1


class Radar:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def _all_positions(self):
        return [(self.bbox.x0, self.bbox.y0),
                (self.bbox.x0, self.bbox.y1),
                (self.bbox.x1, self.bbox.y1),
                (self.bbox.x1, self.bbox.y1)]

    def solve_range(self):
        max_range = 0
        for position in self._all_positions():
            position = np.array(position)
            r = np.linalg.norm(self.T[:2] - position)
            max_range = max(r, max_range)

        return max_range

    def solve_image_resolution(self):
        area = abs(self.bbox.y1 - self.bbox.y0) \
             * abs(self.bbox.x1 - self.bbox.x0)
        return area / RESOLUTION_CALIBRATION_SIZE  * RESOLUTION_CALIBRATION_BASE

    def plot_image_origin(self, ax):
        positions = self._all_positions()
        (min_x, min_y) = positions[0]

        for (x, y) in positions[1:]:
            min_x = min(min_x, x)
            min_y = min(min_y, y)

        ax.add_artist(patches.Ellipse((min_x, min_y),
                                       1,
                                       1,
                                       alpha=0.5,
                                       color=self.color))
        ax.text(min_x, min_y, 'ImageModel.origin', color=self.color)


    def draw(self, target_range, ax, fig):
        ax.add_artist(patches.Rectangle((self.bbox.x0,  self.bbox.y0),
                                         self.bbox.x1 - self.bbox.x0,
                                         self.bbox.y1 - self.bbox.y0,
                                         color=self.color,
                                         alpha=0.3))
        ax.add_artist(patches.Rectangle((self.bbox.x0,  self.bbox.y0),
                                         self.bbox.x1 - self.bbox.x0,
                                         self.bbox.y1 - self.bbox.y0,
                                         color=self.color,
                                         alpha=0.3))
        self.draw_lines(target_range, ax)
        resolution = self.solve_image_resolution()
        ax.text(self.bbox.x1, self.bbox.y1, 'grid resolution = %0.4f' % resolution,
                color=self.color)

        range_resolution = target_range / 1024
        ax.text(self.bbox.x1, self.bbox.y1 - 1, 'range resolution = %0.4f' % range_resolution,
                color=self.color)
        self.plot_image_origin(ax)


    def draw_lines(self, target_range, ax):
        rotl    = quaternion_matrix(quaternion_about_axis(-self.beam_width / 2, [0, 0, 1]))
        rotr    = quaternion_matrix(quaternion_about_axis(+self.beam_width / 2, [0, 0, 1]))
        unit_z  = np.array([0, 0, 1])
        unit0db = self.R @ unit_z

        a = rotl @ unit0db
        unit3db = [rotl @ unit0db, rotr @ unit0db]

        theta_0db = np.arctan2(unit0db[1], unit0db[0])
        theta_3db = [np.arctan2(u[1], u[0]) for u in unit3db]

        # 1.  Draw a round dot where the radar is .
        ax.add_artist(patches.Ellipse((self.T[0], self.T[1]), 0.2, 0.2, color=self.color))

        # 2.a Draw a thick line to it's 0db loss line.
        ax.arrow(self.T[0],
                 self.T[1],
                 np.cos(theta_0db) * target_range,
                 np.sin(theta_0db) * target_range,
                 color=self.color,
                 alpha=0.5)

        # 2.b Draw a thick line to it's 3db loss lines.
        for angle in theta_3db:
            ax.arrow(self.T[0],
                     self.T[1],
                     np.cos(angle) * target_range,
                     np.sin(angle) * target_range,
                     color=self.color,
                     alpha=0.25)

def main():
    squint_rhs = \
        Radar(T=np.array([+0.1163, +0.5644, -0.0647]),
              R=quaternion_matrix([0.6553282, 0.6553282, 0.270597, 0.270597]),
              name='shannon_squint_rhs',
              color='blue',
              bbox=Bbox(x0=2, y0=-2, x1=65, y1=-20),
              beam_width=np.deg2rad(60))
    squint_lhs = \
        Radar(T=np.array([+0.1273, -0.5754, -0.0647]),
              R=quaternion_matrix([0.270597, 0.270597, 0.6553282, 0.6553282]),
              name='shannon_squint_lhs',
              color='red',
              bbox=Bbox(x0=2, y0=+2, x1=65, y1=+20),
              beam_width=np.deg2rad(60))
    broad_lhs = \
        Radar(T=np.array([-0.2069, 0.4545, -0.0647]),
              R=quaternion_matrix([0, 0, 0.707107, 0.707107]),
              name='shannon_broad_lhs',
              color='green',
              bbox=Bbox(x0=-15, y0=+2, x1=25, y1=+25),
              beam_width=np.deg2rad(60))
    #radars = [squint_rhs, squint_lhs, broad_lhs]
    radars = [squint_rhs, squint_lhs]


    # Prepare a plot
    fig, ax = plt.subplots()

    # Find the maximum distance from the origin and set that to be the dimension.
    max_x = 0
    max_y = 0
    max_range = 0
    for radar in radars:
        max_x = max(max_x, abs(radar.bbox.x0), abs(radar.bbox.x1))
        max_y = max(max_y, abs(radar.bbox.y0), abs(radar.bbox.y1))
        max_range = max(max_range, radar.solve_range())

    ax.grid()
    ax.axis('equal')
    ax.set_title('Imaging Configuration in Vehicle Coordinates')
    ax.set_xlim(-max_x - 1, +max_x + 1)
    ax.set_xlabel('X (meters)')
    ax.set_ylim(-max_y - 1, +max_y + 1)
    ax.set_ylabel('Y (meters)')

    # Draw a car.
    CAR_X = 4.2
    CAR_Y = 1.8
    ax.add_artist(
            patches.Ellipse((0, 0),
                            CAR_X,
                            CAR_Y,
                            color='black',
                            alpha=0.5))

    for radar in radars:
        radar.draw(max_range, ax, fig)


    plt.show()

if __name__ == '__main__':
    main()
