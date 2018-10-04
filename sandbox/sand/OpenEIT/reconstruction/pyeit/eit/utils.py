# coding: utf-8
# pylint: disable=invalid-name
"""
util functions for 2D EIT
1. generate stimulation lines/patterns
"""
# Copyright (c) Benyuan Liu. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
from __future__ import division, absolute_import, print_function

import numpy as np


def eit_scan_lines(ne=16, dist=1):
    """
    generate scan matrix

    Parameters
    ----------
    ne : int
        number of electrodes
    dist  : int
        distance between A and B (default=1)

    Returns
    -------
    ex_mat : NDArray
        stimulation matrix

    Notes
    -----
    in the scan of EIT (or stimulation matrix), we use 4-electrodes
    mode, where A, B are used as positive and negative stimulation
    electrodes and M, N are used as voltage measurements

         1 (A) for positive current injection,
        -1 (B) for negative current sink

    dist is the distance (number of electrodes) of A to B
    in 'adjacent' mode, dist=1, in 'apposition' mode, dist=ne/2

    WARNING
    -------
    ex_mat is local index, where it is ranged from 0...15.
    In FEM applications, you should convert ex_mat to
    global index using el_pos information.

    Examples
    --------
    # let ne=16
    if mode=='neighbor':
        ex_mat = eit_scan_lines()
    elif mode=='apposition':
        ex_mat = eit_scan_lines(dist=8)
    """
    ex = np.array([[i, np.mod(i+dist, ne)] for i in range(ne)])

    return ex


if __name__ == "__main__":
    m = eit_scan_lines(dist=8)
    print(m)
