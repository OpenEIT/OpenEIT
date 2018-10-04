# -*- coding: utf-8 -*-
# pylint: disable=no-member, invalid-name
""" common function for simplex """

from itertools import combinations
import numpy as np


def sim_conv(simplex, n=3):
    """ simplex to any dimension """
    v = [list(combinations(sim, n)) for sim in simplex]
    # change to (num_of_points x n)
    t = np.sort(np.array(v).reshape(-1, n), axis=1)
    # delete duplicated entries
    t_unique = np.unique(t.view([('', t.dtype)] * n)).view(np.uint32)
    return t_unique


def sim2tri(simplex):
    """ convert simplex of high dimension to indices of triangles """
    return sim_conv(simplex, 3)


def sim2edge(simplex):
    """ convert simplex of high dimension to indices of edges """
    return sim_conv(simplex, 2)
