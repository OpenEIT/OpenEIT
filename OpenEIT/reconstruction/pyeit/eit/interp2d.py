# coding: utf-8
# pylint: disable=invalid-name, no-member, too-many-locals, no-name-in-module
""" interpolation on 2D/3D irregular/regular grids """
# Copyright (c) Benyuan Liu. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
from __future__ import division, absolute_import, print_function

import numpy as np
import scipy.linalg as la
from scipy.sparse import coo_matrix
from scipy.spatial import ConvexHull
from matplotlib.path import Path
import matplotlib.pyplot as plt

# for debugging
# from pyeit.mesh import layer_circle, set_perm


def meshgrid(pts, n=32, ext_ratio=0, gc=False):
    """
    build xg, yg, mask grids from triangles point cloud
    function for interpolating regular grids

    Parameters
    ----------
    pts : NDArray
        nx2 array of points (x, y)
    el_pos : NDArray (optional)
        the location of electrodes (for extract the convex hull of pts)
    n : int
        the number of meshgrid per dimension
    ext_ratio : float
        extend the boundary of meshgrid by ext_ratio*d
    gc : bool
        grid_correction, offset xgrid and ygrid by half step size

    Notes
    -----
    mask denotes points outside mesh.
    """
    xg, yg = _build_grid(pts, n=n, ext_ratio=ext_ratio, gc=gc)
    # pts_edges = pts[el_pos]
    pts_edges = _hull_points(pts)
    mask = _build_mask(pts_edges, xg, yg)
    return xg, yg, mask


def _build_grid(pts, n=32, ext_ratio=0, gc=False):
    """generating mesh grids"""
    x, y = pts[:, 0], pts[:, 1]
    x_min, x_max = min(x), max(x)
    y_min, y_max = min(y), max(y)
    x_ext = (x_max - x_min) * ext_ratio
    y_ext = (y_max - y_min) * ext_ratio
    xv, xv_step = np.linspace(x_min-x_ext, x_max+x_ext, num=n,
                              endpoint=False, retstep=True)
    yv, yv_step = np.linspace(y_min-y_ext, y_max+y_ext, num=n,
                              endpoint=False, retstep=True)
    # if need grid correction
    if gc:
        xv = xv + xv_step / 2.0
        yv = yv + yv_step / 2.0
    xg, yg = np.meshgrid(xv, yv, sparse=False, indexing='xy')
    return xg, yg


def _build_mask(pts_edges, xg, yg):
    """find whether meshgrids is interior of mesh"""
    # 1. create mask based on meshes
    points = np.vstack((xg.flatten(), yg.flatten())).T

    # 2. extract edge points using el_pos
    path = Path(pts_edges, closed=False)
    mask = path.contains_points(points)

    return ~mask


def _hull_points(pts):
    """return the convex hull points"""
    cv = ConvexHull(pts)
    hull_nodes = cv.vertices
    return pts[hull_nodes, :]


def _distance2d(x, y, center='mean'):
    """
    Calculate radius given center.
    This function can be OPTIMIZED using numba or cython.
    """
    if center is None:
        xc, yc = 0, 0
    elif center == 'mean':
        xc, yc = np.mean(x), np.mean(y)
    else:
        xc, yc = center[0], center[1]

    d = np.sqrt((x-xc)**2 + (y-yc)**2).ravel()
    return d


def _distance_matrix2d(xy, xyi):
    """
    Description
    -----------
    (2D only)
    return element-wise distance matrix (pair-wise)
    """
    # Make a distance matrix between pairwise observations
    # Note: from <http://stackoverflow.com/questions/1871536>
    # (Yay for ufuncs!)
    d0 = np.subtract.outer(xy[:, 0], xyi[:, 0])  # size(xy) * size(xyi)
    d1 = np.subtract.outer(xy[:, 1], xyi[:, 1])

    # hypot : element-wise sqrt(d0**2 + d1**2)
    return np.hypot(d0, d1)


def weight_sigmod(xy, xyi, ratio=0.05, s=20.0):
    """
    Description
    -----------
    (2D only)
    local weight/interpolate by sigmod function (GREIT3D)

    Parameters
    ----------
    xy : NDArray
        (x, y) of values
    xyi : NDArray
        (xi, yi) of interpolated locations
    ratio : float
        R0 = d_max * ratio
    s : float
        control the decay ratio

    Returns
    -------
    w_mat : NDArray
        weighting matrix mapping from xy to xyi (xy meshgrid)
    """
    d_mat = _distance_matrix2d(xy, xyi)
    # normalize distance
    d_max = np.max(d_mat)
    d_mat = 5.0 * d_mat / d_max
    # desired radius (a ratio of max pairwise distance)
    r0 = 5.0 * ratio
    # weights is the sigmod function
    weight = 1./(1 + np.exp(s*(d_mat - r0)))
    # normalized
    w_mat = weight / weight.sum(axis=0)

    return w_mat


def weight_idw(xy, xyi, k=6, p=1.):
    """
    Description
    -----------
    (2D only)
    local weight/interpolate by inverse distance

    Parameters
    ----------
    xy : NDArray
        (x, y) of values
    xyi : NDArray
        (xi, yi) of interpolated locations
    k : int
        number of nearest neighbores
    p : float
        scaling distance

    Returns
    -------
    w_mat : NDArray
        weighting matrix mapping from xy to xy_mesh
    """
    d_mat = _distance_matrix2d(xy, xyi)
    # weight = 1.0 / d_mat**p
    weight = 1.0/d_mat**p
    # keep only k largest neighbores (nearest)
    for w in weight.T:
        sort_indices = np.argsort(w)
        np.put(w, sort_indices[:-k], 0)
    # normalized
    w_mat = weight / weight.sum(axis=0)

    # xy times xyi size, use w_mat.T to multiply
    return w_mat


def weight_linear_rbf(xy, xyi, z):
    """
    Description
    -----------
    (2D only)
    local weight/interpolate by linear rbf function (z value required)

    Parameters
    ----------
    xy : NDArray
        (x, y) of values
    xyi : NDArray
        (xi, yi) of interpolated locations

    Returns
    -------
    w_mat : NDArray
        weighting matrix mapping from xy to xy_mesh
    """
    internal_dist = _distance_matrix2d(xy, xy)
    weights = la.solve(internal_dist, z)

    interp_dist = _distance_matrix2d(xy, xyi)
    zi = np.dot(interp_dist.T, weights)

    return zi


def weight_barycentric_gradient():
    """
    Description
    -----------
    (2D only)
    local weight/interpolate by barycentric gradient

    Parameters
    ----------
    xy : NDArray
        (x, y) of values
    xyi : NDArray
        (xi, yi) of interpolated locations

    Returns
    -------
    w_mat : NDArray
        weighting matrix mapping from xy to xy_mesh
    """
    pass


def sim2pts(pts, sim, sim_values):
    """
    Description
    -----------
    (2D/3D) compatible.

    Interp values on points using values on simplex,
    a simplex can be triangle or tetrahedron.
    The areas/volumes are used as weights.

    f_n = (sum_e r_e*S_e) / (sum_e S_e)

    where r_e is the value on triangles who share the node n,
    S_e is the area of triangle e.

    Notes
    -----
    This function is similar to pdeprtni of MATLAB pde.
    """
    N = pts.shape[0]
    M, dim = sim.shape
    # calculate the weights
    # triangle/tetrahedron must be CCW (recommended), then a is positive
    if dim == 3:
        weight_func = tri_area
    elif dim == 4:
        weight_func = tet_volume
    weights = weight_func(pts, sim)
    # build tri->pts matrix, could be accelerated using sparse matrix
    row = np.ravel(sim)
    col = np.repeat(np.arange(M), dim)  # [0, 0, 0, 1, 1, 1, ...]
    data = np.repeat(weights, dim)
    e2n_map = coo_matrix((data, (row, col)), shape=(N, M)).tocsr()
    # map values from elements to nodes
    # and re-weight by the sum of the areas/volumes of adjacent elements
    f = e2n_map.dot(sim_values)
    w = np.sum(e2n_map.toarray(), axis=1)

    return f/w


def pts2sim(sim, pts_values):
    """
    Description
    -----------
    (2D/3D) compatible.

    Given values on nodes, calculate interpolated values on simplex,
    this function was tested and equivalent to MATLAB 'pdeintrp'
    except for the shapes of 'pts' and 'tri'

    Parameters
    ----------
    sim : NDArray
        Mx3, Mx4 array, elements or simplex
        triangles denote connectivity [[i, j, k]]
        tetrahedrons denote connectivity [[i, j, m, n]]
    pts_values : NDArray
        Nx1 array, real/complex valued

    Returns
    -------
    el_value: NDArray
        Mx1 array, real/complex valued

    Notes
    -----
    This function is similar to pdfinterp of MATLAB pde.
    """
    # averaged over 3 nodes of a triangle
    el_value = np.mean(pts_values[sim], axis=1)
    return el_value


def tri_area(pts, sim):
    """
    calculate the area of each triangle

    Parameters
    ----------
    pts : NDArray
        Nx2 array, (x,y) locations for points
    sim : NDArray
        Mx3 array, elements (triangles) connectivity

    Returns
    -------
    a : NDArray
        Areas of triangles
    """
    a = np.zeros(np.shape(sim)[0])
    for i, e in enumerate(sim):
        xy = pts[e]
        # s1 = xy[2, :] - xy[1, :]
        # s2 = xy[0, :] - xy[2, :]
        # s3 = xy[1, :] - xy[0, :]
        # which can be simplified to
        # s = xy[[2, 0, 1]] - xy[[1, 2, 0]]
        s = xy[[2, 0]] - xy[[1, 2]]

        # a should be positive if triangles are CCW arranged
        a[i] = la.det(s)

    return a * 0.5


def tet_volume(pts, sim):
    """
    calculate the area of each triangle

    Parameters
    ----------
    pts : NDArray
        Nx3 array, (x,y, z) locations for points
    sim : NDArray
        Mx4 array, elements (tetrahedrons) connectivity

    Returns
    -------
    v : NDArray
        Volumes of tetrahedrons
    """
    v = np.zeros(np.shape(sim)[0])
    for i, e in enumerate(sim):
        xyz = pts[e]
        s = xyz[[2, 3, 0]] - xyz[[1, 2, 3]]

        # a should be positive if triangles are CCW arranged
        v[i] = la.det(s)

    return v / 6.0


def pdetrg(pts, tri):
    """
    Description
    -----------
    (Deprecated)
    analytical calculate the Area and grad(phi_i) using
    barycentric coordinates (simplex coordinates)
    this function is tested and equivalent to MATLAB 'pdetrg'
    except for the shape of 'pts' and 'tri' and the output

    note: each node may have multiple gradients in neighbor
    elements' coordinates. you may averaged all the gradient to
    get one node gradient.

    Parameters
    ----------
    pts : NDArray
        Nx2 array, (x,y) locations for points
    tri : NDArray
        Mx3 array, elements (triangles) connectivity

    Returns
    -------
    a : NDArray
        Mx1 array, areas of elements
    grad_phi_x : NDArray
        Mx3 array, x-gradient on elements' local coordinate
    grad_phi_y : NDArray
        Mx3 array, y-gradient on elements' local coordinate
    """
    m = np.size(tri, 0)

    ix = tri[:, 0]
    iy = tri[:, 1]
    iz = tri[:, 2]

    s1 = pts[iz, :] - pts[iy, :]
    s2 = pts[ix, :] - pts[iz, :]
    s3 = pts[iy, :] - pts[ix, :]

    a = 0.5*(s2[:, 0]*s3[:, 1] - s3[:, 0]*s2[:, 1])
    if any(a) < 0:
        exit("triangles should be given in CCW order")

    # note in python, reshape place elements first on the right-most index
    grad_phi_x = np.reshape([-s1[:, 1] / (2. * a),
                             -s2[:, 1] / (2. * a),
                             -s3[:, 1] / (2. * a)], [-1, m]).T
    grad_phi_y = np.reshape([s1[:, 0] / (2. * a),
                             s2[:, 0] / (2. * a),
                             s3[:, 0] / (2. * a)], [-1, m]).T

    return a, grad_phi_x, grad_phi_y


def pdegrad(pts, tri, node_value):
    """
    Description
    -----------
    (Deprecated)
    given values on nodes, calculate the averaged-grad on elements
    this function was tested and equivalent to MATLAB 'pdegrad'
    except for the shape of 'pts', 'tri'

    Parameters
    ----------
    pts : NDArray
        Nx2 array, (x,y) locations for points
    tri : NDArray
        Mx3 array, elements (triangles) connectivity
    node_value : NDArray
        Nx1 array, real/complex valued

    Returns
    -------
    NDArray
        el_grad, Mx2 array, real/complex valued
    """
    m = np.size(tri, 0)
    _, grad_phi_x, grad_phi_y = pdetrg(pts, tri)
    tri_values = np.reshape(node_value[tri.ravel()], [m, -1])
    grad_el_x = np.sum(grad_phi_x * tri_values, axis=1)
    grad_el_y = np.sum(grad_phi_y * tri_values, axis=1)
    return grad_el_x, grad_el_y


def demo():
    """demo shows how to interpolate on regular/irregular grids"""
    # 1. create mesh
    mesh_obj, _ = layer_circle(n_layer=8, n_fan=6)
    pts = mesh_obj['node']
    tri = mesh_obj['element']

    # set anomaly
    anomaly = [{'x': 0.5, 'y': 0.5, 'd': 0.2, 'perm': 100.0}]
    mesh_new = set_perm(mesh_obj, anomaly=anomaly)

    # 2. interpolate using averaged neighbor triangle area
    perm_node = sim2pts(pts, tri, mesh_new['perm'])

    # plot mesh and interpolated mesh (tri2pts)
    fig_size = (6, 4)
    fig = plt.figure(figsize=fig_size)
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    ax.triplot(pts[:, 0], pts[:, 1], tri)
    im1 = ax.tripcolor(pts[:, 0], pts[:, 1], tri, mesh_new['perm'])
    fig.colorbar(im1, orientation='vertical')

    fig = plt.figure(figsize=fig_size)
    ax2 = fig.add_subplot(111)
    ax2.set_aspect('equal')
    ax2.triplot(pts[:, 0], pts[:, 1], tri)
    im2 = ax2.tripcolor(pts[:, 0], pts[:, 1], tri, perm_node, shading='flat')
    fig.colorbar(im2, orientation='vertical')

    # 3. interpolate on grids (irregular or regular) using IDW, sigmod
    xg, yg, mask = meshgrid(pts)
    im = np.ones_like(mask)
    # mapping from values on xy to values on xyi
    xy = np.mean(pts[tri], axis=1)
    xyi = np.vstack((xg.flatten(), yg.flatten())).T
    # w_mat = weight_idw(xy, xyi)
    w_mat = weight_sigmod(xy, xyi)
    im = np.dot(w_mat.T, mesh_new['perm'])
    # im = weight_linear_rbf(xy, xyi, mesh_new['perm'])
    im[mask] = 0.
    # reshape to grid size
    im = im.reshape(xg.shape)

    # plot interpolated values
    fig, ax = plt.subplots(figsize=fig_size)
    ax.set_aspect('equal')
    ax.triplot(pts[:, 0], pts[:, 1], tri, alpha=0.5)
    im3 = ax.pcolor(xg, yg, im, edgecolors=None, linewidth=0, alpha=0.8)
    fig.colorbar(im3, orientation='vertical')
    plt.show()


if __name__ == "__main__":
    demo()
