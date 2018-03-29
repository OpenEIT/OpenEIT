# coding: utf-8
# pylint: disable=invalid-name, no-member, too-many-locals
""" plot function for distmesh 2d and 3d """
from __future__ import absolute_import

import matplotlib
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np

from ..utils import edge_project, edge_list


def circumcircle(p1, p2, p3):
    """
    The circumcircle is a triangle's circumscribed circle,
    returns (x, y, r) of circumcenter

    Parameters
    ----------
    p1, p2, p3 : array_like
        points

    Note
    ----
    http://www.labri.fr/perso/nrougier/coding/gallery/
    """
    dp1 = p1 - p2
    dp2 = p3 - p1

    mid1 = (p1 + p2) / 2.
    mid2 = (p3 + p1) / 2.

    a = np.array([[-dp1[1], dp2[1]],
                  [dp1[0], -dp2[0]]])
    b = -mid1 + mid2
    s = np.linalg.solve(a, b)
    # extract circumscribed center and radius
    cpc = mid1 + s[0]*np.array([-dp1[1], dp1[0]])
    cr = np.linalg.norm(p1 - cpc)

    return cpc[0], cpc[1], cr


def voronoi(pts, tri, fd=None):
    """
    build voronoi cells using delaunay tessellation

    Parameters
    ----------
    pts : array_like
        points on 2D
    tri : array_like
        triangle structure
    fd : str
        function handler of distances

    Returns
    -------
    array_like
        voronoi cells of lists

    Note
    ----
    adds 'edge-list using signed distance function'
    http://www.labri.fr/perso/nrougier/coding/gallery/
    """
    n = tri.shape[0]

    # Get circle for each triangle, center will be a voronoi cell point
    cells = []
    for i in range(pts.shape[0]):
        cells.append(list())

    def extract_xy(e):
        """ append center (x,y) of triangle-circumcircle to the cell list """
        p1, p2, p3 = pts[tri[e]]
        xc, yc, _ = circumcircle(p1, p2, p3)
        return [xc, yc]

    # list(map(extract_xy, range(n)))
    pc = np.array([extract_xy(i) for i in range(n)])

    # project point on the boundary if it is outside, where fd(p) > 0
    # this happens when low-quality mesh is generated.
    if fd is not None:
        d = fd(pc)
        ix = d > 0
        pc[ix] -= edge_project(pc[ix], fd)

    # build cells enclosing points
    for i in range(n):
        pc_tuple = tuple(pc[i])
        cells[tri[i, 0]].append(pc_tuple)
        cells[tri[i, 1]].append(pc_tuple)
        cells[tri[i, 2]].append(pc_tuple)

    # append middle (x, y) of edge-bars to the cells,
    # make a closed patch of the voronoi tessellation.
    # note : it may be better if you project this point on fd
    edge_bars = edge_list(tri)
    h_bars = np.mean(pts[edge_bars], axis=1)
    if fd is not None:
        h_bars -= edge_project(h_bars, fd)
    for i, bars in enumerate(edge_bars):
        cells[bars[0]].append(tuple(h_bars[i]))
        cells[bars[1]].append(tuple(h_bars[i]))

    x = pts[:, 0]
    y = pts[:, 1]
    # Reordering cell points in trigonometric way
    for i, cell in enumerate(cells):
        xy = np.array(cell)
        angles = np.arctan2(xy[:, 1]-y[i], xy[:, 0]-x[i])
        s = np.argsort(angles)
        cell = xy[s].tolist()
        cell.append(cell[0])
        cells[i] = cell

    return cells


def voronoi_plot(pts, tri, figsize=(6, 4), val=None, fd=None):
    """ plot voronoi diagrams on bounded shape

    Parameters
    ----------
    pts : array_like
        points on 2D
    tri : array_like
        triangle structure
    val : array_like, optional
        values on nodes
    fd : str, optional
        function handler

    Returns
    -------
    fig : str
        figure handler
    ax : str
        axis handler

    Note
    ----
    adds 'maps value to colormap', see
    http://www.labri.fr/perso/nrougier/coding/gallery/
    """
    cells = voronoi(pts, tri, fd)

    # map values on nodes to colors
    if val is None:
        val = np.random.rand(pts.shape[0])
    norm = matplotlib.colors.Normalize(vmin=min(val),
                                       vmax=max(val), clip=True)
    mapper = cm.ScalarMappable(norm=norm, cmap=cm.Greens)

    fig, ax = plt.subplots(figsize=figsize)
    # draw mesh (optional)
    # ax.triplot(pts[:, 0], pts[:, 1], tri, color='b', alpha=0.50, lw=0.5)
    # ax.scatter(pts[:, 0], pts[:, 1], s=3, color='r', zorder=1)

    # draw voronoi tessellation
    for i, cell in enumerate(cells):
        codes = [matplotlib.path.Path.MOVETO] \
              + [matplotlib.path.Path.LINETO] * (len(cell)-2) \
              + [matplotlib.path.Path.CLOSEPOLY]
        path = matplotlib.path.Path(cell, codes)
        # map values on nodes to colormap
        # e.g., color = np.random.uniform(.4, .9, 3)
        color = mapper.to_rgba(val[i])
        # using patches to plot the voronoi of a node
        patch = matplotlib.patches.PathPatch(path, facecolor=color,
                                             edgecolor='w', zorder=-1,
                                             lw=0.4)
        ax.add_patch(patch)

    ax.set_aspect('equal')
    return fig, ax
