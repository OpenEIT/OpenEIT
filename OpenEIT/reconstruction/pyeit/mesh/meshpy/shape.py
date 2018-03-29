# pylint: disable=no-member, invalid-name
""" generate basic shapes, anomaly patterns for meshpy """
# Copyright (c) Benyuan Liu. All rights reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

import numpy as np


def throx(num_poly):
    """
    draw 'throx' outline (points)
    codes copied from A. F. Schkarbanenko EIT2D MATLAB

    <input>
    num_poly : number of nodes on the outer facet

    <output>
    points : points locations on the facet
    npoints : the length of the facet
    """
    r1 = [2.5, 3.0, 3.2, 3.3, 3.5, 3.8, 4.0, 4.2, 4.5, 5.0,
          5.4, 5.6, 5.6, 5.6, 5.5, 5.4, 5.2, 5.1, 5.0, 4.8,
          4.7, 4.6, 4.6, 4.5, 4.5, 4.5, 4.4, 4.3, 4.1, 3.95,
          3.8, 3.7, 3.6, 3.3, 3.2]
    r2 = list(r1)
    r2.reverse()
    r = [2.0] + r1 + [2.0] + r2
    # r is NOT continuous, we normalize 'r' first
    r = np.array(r)
    r = r/r.max()
    angles = np.linspace(0, 2*np.pi, len(r), endpoint=False) - np.pi/2.

    # next, we do DFT transform of the curvature r and
    # keep the lowest 7-coeffs, as a digital 'low-pass' filter
    # to make the throx more smooth
    kmax = 8
    a = np.zeros(kmax)
    b = np.zeros(kmax)
    for i in range(kmax):
        a[i] = np.dot(r, np.cos(i*angles)) / float(len(r))
        b[i] = np.dot(r, np.sin(i*angles)) / float(len(r))

    # now we re-build (IFFT) low-passed throx curve
    t_poly = np.zeros(num_poly)
    angles = np.linspace(0, 2*np.pi, num_poly, endpoint=False) - np.pi/2.
    for i in range(kmax):
        t_poly = t_poly + a[i]*np.cos(i*angles) + b[i]*np.sin(i*angles)

    # generate points for mesh2d
    pts = [(ri*np.cos(ai), ri*np.sin(ai)) for (ai, ri) in zip(angles, t_poly)]
    n = [np.size(pts, 0)]
    return pts, n


def disc(num_poly):
    """
    draw a disc outline (circle

    <input>
    num_poly : number of nodes on the outer facet

    <output>
    points : points locations on the facet
    npoints : the length of the facet
    """
    angles = np.linspace(0, 2*np.pi, num_poly, endpoint=False)
    points = [(np.cos(a), np.sin(a)) for a in angles]
    npoints = [np.size(points, 0)]
    return points, npoints


def disc_anomaly(num_poly):
    """
    a simple disc shape with refined anomaly region

    Notes
    -----
    generate 'disc-anomaly' example, inhomogenious regions
    codes copied from A. F. Schkarbanenko EIT2D MATLAB

    <input>
    num_poly : number of nodes on the outer facet

    <output>
    points : points generated for the inhomogenious regions
    npoints : the length of each facet
    """
    points, npoints = disc(num_poly)
    # Anomaly: kite
    phi = np.linspace(0, 2*np.pi, 20, endpoint=False)
    anomaly = [(0.15*(np.cos(p) + 0.65*np.cos(2*p)),
                0.15*(1.5*np.sin(p)) - 1./3) for p in phi]
    # append
    points.extend(anomaly)
    npoints = npoints + [np.size(points, 0)]
    return points, npoints


# a throx shape with refined anomaly region
def throx_anomaly(num_poly):
    """
    generate 'throx-anomaly' example, inhomogenious regions
    codes copied from A. F. Schkarbanenko EIT2D MATLAB

    <input>
    num_poly : number of nodes on the outer facet

    <output>
    points : points generated for the inhomogenious regions
    npoints : the length of each facet
    """
    points, npoints = throx(num_poly)
    # Heart
    phi = np.linspace(0, 2*np.pi, 12, endpoint=False)
    anomaly = [(1./6*np.cos(p), 1./6*np.sin(p)+1./4) for p in phi]
    points.extend(anomaly)
    npoints.extend([np.size(points, 0)])
    # bone
    ax = 0.4*np.array([-1./4, 0, 1./4, 0])
    ay = 0.4*np.array([-1./2, -1./4, -1./2, -3./4]) - 1./7
    anomaly = [(x, y) for (x, y) in zip(ax, ay)]
    points.extend(anomaly)
    npoints.extend([np.size(points, 0)])
    # Lung left
    phi = np.linspace(0, 2*np.pi, 14, endpoint=False)
    anomaly = [(1./4*np.cos(p) + 1./2.5, 1./3*np.sin(p)) for p in phi]
    points.extend(anomaly)
    npoints.extend([np.size(points, 0)])
    # Lung right
    phi = np.linspace(0, 2*np.pi, 14, endpoint=False)
    anomaly = [(1./4*np.cos(p) - 1./2.5, 1./3*np.sin(p)) for p in phi]
    points.extend(anomaly)
    npoints.extend([np.size(points, 0)])

    return points, npoints


# generate anomaly patterns with regional IDs
# numel of 'perm' must match numel 'ID'
def anomaly_perm(mesh, curve='disc-anomaly'):
    """
    append anomaly permitivity on mesh obj
    <format> ID : sigma
    only 'disc-anomaly' and 'throx-anomaly' are supported
    """
    if curve == 'disc-anomaly':
        perm = {0: 1,       # background
                1: 5+0.1j}  # anomaly

    else:
        perm = {0: 0.33,        # background
                1: 0.7+0.01j,   # heart
                2: 0.02,        # bone
                3: 0.0971,      # left-lung
                4: 0.0971}      # right-lung

    # place permitivity on 'triangle' meshes
    eleID = np.array(mesh.element_attributes, dtype='int')
    tri_perm = np.array([perm[eleID[i]] for i in range(len(eleID))])

    return tri_perm
