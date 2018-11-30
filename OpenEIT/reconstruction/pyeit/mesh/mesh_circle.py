# coding: utf-8
# pylint: disable=invalid-name, no-member, too-many-locals
""" create multi-layered mesh on a unit circle """
# Copyright (c) Benyuan Liu. All rights reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
from __future__ import division, absolute_import, print_function

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


class MeshCircle(object):
    """ create meshes on uniform circle """

    def __init__(self, n_fan=6, n_layer=8, n_el=16):
        """
        Parameters
        ----------
        n_fan : int
            number of fans (see the inner most layer)
        n_layer : int
            number of layers
        n_el : int
            number of boundary electrodes (default: 16)
        """
        self.n_fan = n_fan
        self.n_layer = n_layer
        self.n_el = n_el

        # number of points per-layer
        pts_per_layer = self.n_fan * np.arange(self.n_layer+1)
        # The number of points of the initial layer (center point: 1 node)
        pts_per_layer[0] = 1
        self.pts_per_layer = pts_per_layer

        # starting point index of each layer
        # the initial layer (put at [-1]) must start with 0
        index = np.cumsum(pts_per_layer)
        index[-1] = 0
        self.index_per_layer = index

    def create(self):
        """ create pts and tri """
        pts = self._spawn_points()
        tri = self._spawn_elements()
        el_pos = self._get_electrodes()
        return pts, tri, el_pos

    def update(self, n_fan=8, n_layer=6, n_el=16):
        """ update parameters """
        self.n_fan = n_fan
        self.n_layer = n_layer
        self.n_el = n_el

    def _get_electrodes(self):
        """ return the numbering of electrodes """
        el_start = self.index_per_layer[self.n_layer-1]
        el_len = self.pts_per_layer[self.n_layer]

        # place electrodes uniformly on the boundary
        n = np.linspace(el_start, el_start + el_len, num=self.n_el,
                        endpoint=False, dtype=np.int)

        # for FMMU, electrodes should be placed clockwise
        # with 1 on the right (x+)
        n = n[::-1]  # reverse the order of electrodes
        n = np.roll(n, 1)  # rotate the index by 1
        return n

    def _spawn_points(self):
        """ generate points """
        # init points
        p = [0, 0]

        # divide r uniformly axial
        delta_r = 1. / self.n_layer

        for i in range(1, self.n_layer+1):
            # increment points per-layer by fans
            n = i*self.n_fan
            r = i*delta_r
            # generate points on a layer
            pts = r * self._points_on_circle(n, offset=i)
            p = np.vstack([p, pts])

        return p

    @staticmethod
    def _points_on_circle(n, offset=0, offset_enabled=False):
        """ generate points on unit circle """
        fan_angle = 2*np.pi / n
        a = np.array([i*fan_angle for i in range(n)])
        if offset_enabled:
            a += offset * (fan_angle / 2.)
        pts = np.array([np.cos(a), np.sin(a)]).T

        return pts

    def _spawn_elements(self):
        """ connect points fan-by-fan using a fixed pattern """

        # element connections
        e = []
        for i in range(self.n_layer):
            e_layer = self._connect_layer(i)
            e.append(e_layer)

        return np.vstack(e)

    def _connect_layer(self, i):
        """
        generate connections on the i-th layer using points
        on the i-th and (i-1)-the layers.

        Notes
        -----
        make sure the triangles are counter-clock-wise (CCW)
        """

        # points per layer (ppl) in current and previous layer
        ppl_now = self.pts_per_layer[i + 1]
        ppl_pre = self.pts_per_layer[i]

        # starting index of current and previous layer
        index_now = self.index_per_layer[i]
        index_pre = self.index_per_layer[i-1]

        e = []
        # A circle is divided into multiple fans, we assume that
        # points per layer per fan (plpf) is monotonically increasing
        point_plpf = i + 1
        # The connectivity pattern is the same for every fan,
        # but is different regarding whether the outer point (outer_now) is
        # interior point or boundary point on the current layer of a fan.
        # When the outer point is on the boundary,
        # the inner points (inner_now) is shared by adjacent fans,
        # thus k is not increasing and inner_now is reused.
        k = 0
        for j in range(ppl_now):

            # circular numbering in current layer
            outer_now = index_now + j
            outer_next = index_now + (j + 1) % ppl_now

            # circular numbering in previous layer
            inner_now = index_pre + k
            inner_next = index_pre + (k + 1) % ppl_pre

            # every (ppl_now/n_fan) points
            mode = (j % point_plpf)
            if mode == 0:
                # outer points is on the boundary
                ei = [outer_now, outer_next, inner_now]
                e.append(ei)
            else:
                # outer points is the interior points of a fan
                ei = [inner_now, outer_now, inner_next]
                e.append(ei)
                ei = [outer_now, outer_next, inner_next]
                e.append(ei)
                # advance k when outer points is a interior point
                k += 1

        return e


def demo():
    """ demo using unit_circle_mesh """
    model = MeshCircle()
    p, e, el_pos = model.create()

    # the order of inner-most triangles
    print(e[[0, 1, 2]])

    _, ax = plt.subplots(figsize=(6, 6))
    ax.plot(p[:, 0], p[:, 1], 'ro', markersize=5)
    for i in range(p.shape[0]):
        ax.text(p[i, 0], p[i, 1], str(i))
    ax.set_xlim([-1.2, 1.2])
    ax.set_ylim([-1.2, 1.2])
    ax.grid('on')

    _, ax = plt.subplots(figsize=(6, 6))
    ax.triplot(p[:, 0], p[:, 1], e)
    ax.plot(p[el_pos, 0], p[el_pos, 1], 'ro')
    for i, el in enumerate(el_pos):
        ax.text(p[el, 0], p[el, 1], str(i+1))
    ax.set_xlim([-1.2, 1.2])
    ax.set_ylim([-1.2, 1.2])
    ax.grid('on')

    plt.show()


if __name__ == "__main__":
    demo()
