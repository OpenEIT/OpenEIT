# coding: utf-8
# pylint: disable=invalid-name, too-many-arguments
# pylint: disable=too-many-instance-attributes
"""
This is a python code template that guide you through
writing your own reconstruction algorithms.
"""
# Copyright (c) Benyuan Liu. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
from __future__ import division, absolute_import, print_function

import numpy as np

from .fem import Forward
from .utils import eit_scan_lines


class EitBase(object):
    """
    A base EIT solver.
    """

    def __init__(self, mesh, el_pos, ex_mat=None, step=1, perm=None,
                 jac_normalized=False, parser='std'):
        """
        Parameters
        ----------
        mesh : dict
            mesh structure
        el_pos : array_like
            position (numbering) of electrodes
        ex_mat : array_like, optional (default: opposition)
            2D array, each row is one stimulation pattern/line
        step : int, optional
            measurement method
        perm : array_like, optional
            initial permittivity in generating Jacobian
        jac_normalized: Boolean (default is False)
            normalize the jacobian using f0 computed from input perm
        parser : str, optional, default is 'std'
            parsing file format

        Notes
        -----
        parser is required for your code to be compatible with
        (a) simulation data set or (b) FMMU data set
        """
        if ex_mat is None:
            ex_mat = eit_scan_lines(len(el_pos), 8)
        if perm is None:
            perm = mesh['perm']

        # build forward solver
        fwd = Forward(mesh, el_pos)
        self.fwd = fwd

        # solving mesh structure
        self.mesh = mesh
        self.pts = mesh['node']
        self.tri = mesh['element']

        # shape of the mesh
        self.no_num, self.n_dim = self.pts.shape
        self.el_num, self.n_vertices = self.tri.shape
        self.el_pos = el_pos
        self.parser = parser

        # user may specify a scalar for uniform permittivity
        if np.size(perm) == 1:
            self.perm = perm * np.ones(self.el_num)
        else:
            self.perm = perm

        # solving configurations
        self.ex_mat = ex_mat
        self.step = step

        # solving Jacobian using uniform sigma distribution
        res = fwd.solve_eit(ex_mat, step=step, perm=self.perm, parser=self.parser)
        self.J, self.v0, self.B = res.jac, res.v, res.b_matrix

        # Jacobian normalization: divide each row of J (J[i]) by abs(v0[i])
        if jac_normalized:
            self.J = self.J / np.abs(self.v0[:, None])

        # mapping matrix
        self.H = self.B

        # initialize other parameters
        self.params = {}
        self.xg = []
        self.yg = []
        self.mask = []
        self.setup()

    def setup(self):
        """ setup EIT solver """
        raise NotImplementedError

    def solve(self):
        """ dynamic EIT """
        raise NotImplementedError

    def map(self):
        """ simple mat using projection matrix """
        raise NotImplementedError

    @staticmethod
    def normalize(v1, v0):
        """
        methods of normalizing boundary measurements using
        the amplitude of the reference frame
        """
        dv = (v1 - v0) / np.abs(v0)
        return dv
