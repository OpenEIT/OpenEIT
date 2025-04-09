# coding: utf-8
# pylint: disable=invalid-name, no-member, too-many-arguments
""" wrapper function of distmesh for EIT """
# Copyright (c) Benyuan Liu. All rights reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
from __future__ import division, absolute_import, print_function

import numpy as np

from .distmesh import build
from .mesh_circle import MeshCircle
from .utils import check_order
from .shape import unit_circle, unit_ball, area_uniform
from .shape import fix_points_fd, fix_points_ball


def create(n_el=16, fd=None, fh=None, p_fix=None, bbox=None, h0=0.1):
    """
    wrapper for pyEIT interface

    Parameters
    ----------
    n_el : int, optional
        number of electrodes
    fd : function
        distance function
    fh : function
        mesh size quality control function
    p_fix : NDArray
        fixed points
    bbox : NDArray
        bounding box
    h0 : float, optional
        initial mesh size

    Returns
    -------
    dict
        {'element', 'node', 'perm'}
    """
    if bbox is None:
        bbox = [[-1, -1], [1, 1]]
    # infer dim
    bbox = np.array(bbox)
    n_dim = bbox.shape[1]
    if n_dim not in [2, 3]:
        raise TypeError('distmesh only supports 2D or 3D')
    if bbox.shape[0] != 2:
        raise TypeError('please specify lower and upper bound of bbox')

    if n_dim == 2:
        if fd is None:
            fd = unit_circle
        if p_fix is None:
            p_fix = fix_points_fd(fd, n_el=n_el)
    elif n_dim == 3:
        if fd is None:
            fd = unit_ball
        if p_fix is None:
            p_fix = fix_points_ball(n_el=n_el)

    if fh is None:
        fh = area_uniform

    # 1. build mesh
    p, t = build(fd, fh, pfix=p_fix, bbox=bbox, h0=h0)
    # 2. check whether t is counter-clock-wise, otherwise reshape it
    t = check_order(p, t)
    # 3. generate electrodes, the same as p_fix (top n_el)
    el_pos = np.arange(n_el)
    # 4. init uniform element permittivity (sigma)
    perm = np.ones(t.shape[0], dtype=np.cfloat)
    # 5. build output structure
    mesh = {'element': t,
            'node': p,
            'perm': perm}
    return mesh, el_pos


def set_perm(mesh, anomaly=None, background=None):
    """ wrapper for pyEIT interface

    Note
    ----
    update permittivity of mesh, if specified.

    Parameters
    ----------
    mesh : dict
        mesh structure
    anomaly : dict, optional
        anomaly is a dictionary (or arrays of dictionary) contains,
        {'x': val, 'y': val, 'd': val, 'perm': val}
        all permittivity on triangles whose distance to (x,y) are less than (d)
        will be replaced with a new value, 'perm' may be a complex value.
    background : float, optional
        set background permittivity

    Returns
    -------
    dict
        updated mesh structure
    """
    pts = mesh['element']
    tri = mesh['node']
    perm = mesh['perm'].copy()
    tri_centers = np.mean(tri[pts], axis=1)

    # this code is equivalent to:
    # >>> N = np.shape(tri)[0]
    # >>> for i in range(N):
    # >>>     tri_centers[i] = np.mean(pts[tri[i]], axis=0)
    # >>> plt.plot(tri_centers[:,0], tri_centers[:,1], 'kx')
    n = np.size(mesh['perm'])

    # reset background if needed
    if background is not None:
        perm = background * np.ones(n)

    # change dtype to 'complex' for complex-valued permittivity
    if anomaly is not None:
        for attr in anomaly:
            if np.iscomplex(attr['perm']):
                perm = perm.astype('complex')
                break

    # assign anomaly values (for elements in regions)
    if anomaly is not None:
        for _, attr in enumerate(anomaly):
            d = attr['d']
            # find elements whose distance to (cx,cy) is smaller than d
            if 'z' in attr:
                index = np.sqrt((tri_centers[:, 0] - attr['x'])**2 +
                                (tri_centers[:, 1] - attr['y'])**2 +
                                (tri_centers[:, 2] - attr['z'])**2) < d
            else:
                index = np.sqrt((tri_centers[:, 0] - attr['x'])**2 +
                                (tri_centers[:, 1] - attr['y'])**2) < d
            # update permittivity within indices
            perm[index] = attr['perm']

    mesh_new = {'node': tri,
                'element': pts,
                'perm': perm}
    return mesh_new


def layer_circle(n_el=16, n_fan=8, n_layer=8):
    """ generate mesh on unit-circle """
    model = MeshCircle(n_fan=n_fan, n_layer=n_layer, n_el=n_el)
    p, e, el_pos = model.create()
    perm = np.ones(e.shape[0])

    mesh = {'element': e,
            'node': p,
            'perm': perm}
    return mesh, el_pos
