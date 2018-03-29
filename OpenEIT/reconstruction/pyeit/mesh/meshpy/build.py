# pylint: disable=unused-argument, no-member, too-many-locals, invalid-name
""" create mesh using meshpy """
# Copyright (c) Benyuan Liu. All rights reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

import numpy as np
import scipy.linalg as lp
from matplotlib.path import Path
import matplotlib.pyplot as plt

# call meshpy.triangle
import meshpy.triangle as triangle

# call local shapes
from .shape import disc


def round_trip_connect(start, end):
    """ connect points to facet (standard code in meshpy) """
    return [(i, i+1) for i in range(start, end)] + [(end, start)]


def refinement_func_area(tri_points, area):
    """ refine (equivalent to the max_volume parameter) """
    max_area = 0.005
    return bool(area > max_area)


def refinement_func_location(tri_points, area):
    """
    refine around some locations.
    a tripoints is a ndarray of (x1, y1) (x2, y2) (x3, y3)
    we find its center and return a boolean if this triangle needs refined
    """
    center_tri = np.sum(np.array(tri_points), axis=0)/3.
    max_area = 0.005 + lp.norm(np.abs(center_tri) - 1.0) * 0.05
    return bool(area > max_area)


def refinement_func_anomaly(tri_points, area):
    """
    refine triangles within the anomaly regions.
    you have to specify the points which consist the polygon,
    you need to set the enclosing facet before refining,
    i.e., refinement_func.polygon = polygon

    this function is low-performance
    """
    polygon = Path(refinement_func_anomaly.polygon)
    center_tri = np.sum(np.array(tri_points), axis=0)/3.
    if area > 0.005:
        refine_needed = True
    elif (area > 0.002) and polygon.contains_point(center_tri):
        refine_needed = True
    else:
        refine_needed = False

    return refine_needed


def create(num_el, max_area=0.01, curve=disc, refine=False):
    """
    create 2D mesh for EIT problem,
    num_el is the number of electrodes placed at the boundary

    Parameters
    ----------
    inputs,
        num_el : number of electrodes
        curve : functions of generating curvature
    outputs,
        mesh : mesh object, including
            ['elements'] -> Mx3 ndarray
            ['node']     -> Nx2 ndarray
            ['perm']     -> Mx1 ndarray
        el_pos : the location of electrodes nodes
    """
    # number of interpolate boundary nodes, 4x
    num_poly = 4 * num_el

    # the first #poly points of meshpy's outputs are just the facet
    el_pos = np.arange(0, num_poly, 4)

    # generate 'points' and connect 'facets'
    if not hasattr(curve, '__call__'):
        exit('curvature is not callable, exit')
    points, npoints = curve(num_poly)

    # build facets (link structure l->r)
    lnode = 0
    facets = []
    for rnode in npoints:
        facets.extend(round_trip_connect(lnode, rnode-1))
        lnode = rnode

    # build triangle info
    info = triangle.MeshInfo()
    info.set_points(points)
    info.set_facets(facets)

    # assume the anomaly-region is convex.
    # suppose you want to refine a region in a facet, you can simply specify
    # a (any) point in that region, and the way goes :
    # >>> points [x,y] in region, + region number, + regional area constraints
    # >>> i.e., [0.3, 0.2] + [1] + [0.0001]
    # so the 'only' facet that includes this point will be refined with
    # [0.0001] area constraints and with 'point_markers'=1
    if refine:
        num_regions = len(npoints) - 1
        info.regions.resize(num_regions)
        for i in range(num_regions):
            polygon = points[npoints[i]: npoints[i+1]]
            center_poly = list(np.mean(polygon, axis=0))
            # regional ID start from 1
            info.regions[i] = center_poly + [i+1] + [max_area/2.]

    # build mesh. min_angle can be tweaked, 32.5 is an optimal parameter,
    # you may choose 26.67 for an alternate.
    # you may also pass refinement_func= as your own tweaked refine function
    mesh_struct = triangle.build(info,
                                 max_volume=max_area,
                                 volume_constraints=True,
                                 attributes=True,
                                 quality_meshing=True,
                                 min_angle=32.5)

    # mesh_structure :
    #     points, Nx2 ndarray
    #     point_markers, Nx1 ndarray, 1=boundary, 0=interior
    #     elements, Mx3 ndarray
    #     element_attributes (if refine==True), Mx1 ndarray, triangle markers
    # build output dictionary, initialize with uniform element sigma
    perm = 1. * np.ones(np.shape(mesh_struct.elements)[0])
    mesh = {'element': np.array(mesh_struct.elements),
            'node': np.array(mesh_struct.points),
            'perm': perm}

    return mesh, el_pos


# demo
if __name__ == "__main__":
    # simple
    mesh_obj, e_pos = create(16)

    # show el_pos
    print(mesh_obj)

    # extract 'node' and 'element'
    p = mesh_obj['node']
    t = mesh_obj['element']

    # show the meshes
    plt.plot()
    plt.triplot(p[:, 0], p[:, 1], t)
    plt.plot(p[e_pos, 0], p[e_pos, 1], 'ro')
    plt.axis('equal')
    plt.xlabel('x')
    plt.ylabel('y')
    title_src = 'number of triangles = ' + str(np.size(t, 0)) + ', ' + \
                'number of nodes = ' + str(np.size(p, 0))
    plt.title(title_src)
    plt.show()
