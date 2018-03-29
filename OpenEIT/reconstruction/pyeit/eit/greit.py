# coding: utf-8
# pylint: disable=invalid-name, no-member, too-many-instance-attributes
# pylint: disable=too-many-arguments, arguments-differ
"""
GREIT (using distribution method)

Note, that, the advantages of greit is NOT on simulated data, but
1. construct RM using real-life data with a stick move in the cylinder
2. construct RM on finer mesh, and use coarse-to-fine map for visualization
3. more robust to noise by adding noise via (JJ^T + lamb*Sigma_N)^{-1}
"""
# Copyright (c) Benyuan Liu. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
from __future__ import division, absolute_import, print_function

import numpy as np
import scipy.linalg as la

from .base import EitBase
from .interp2d import meshgrid, weight_sigmod


class GREIT(EitBase):
    """ the GREIT algorithm """

    def setup(self, method='dist', w=None, p=0.20, lamb=1e-2,
              n=32, s=20., ratio=0.1):
        """
        set up for GREIT.

        Parameters
        ----------
        method: str, optional
            'set' or 'dist'
        w: NDArray, optional
            weight on each element
        p: float, optional
            noise covariance
        lamb: float
            regularization parameters
        n: int, optional
            grid size
        s: float, optional
            control the blur
        ratio : float, optional
            desired ratio

        References
        ----------
        .. [1] Bartlomiej Grychtol, Beat Muller, Andy Adler
               "3D EIT image reconstruction with GREIT"
        .. [2] Adler, Andy, et al. "GREIT: a unified approach to
               2D linear EIT reconstruction of lung images."
               Physiological measurement 30.6 (2009): S35.
        """
        # parameters for GREIT projection
        if w is None:
            w = np.ones_like(self.mesh['perm'])
        self.params = {
            'w': w,
            'p': p,
            'lamb': lamb,
            'n': n,
            's': s,
            'ratio': ratio
        }
        # action (currently only support 'dist')
        if method == 'dist':
            w_mat, self.xg, self.yg, self.mask = self._build_grid()
            self.H = self._build_dist(w_mat)
        else:
            raise ValueError('method ' + method + ' not supported yet')

    def solve(self, v1, v0, normalize=False):
        """ solving and interpolating (psf convolve) on grids. """
        if normalize:
            dv = self.normalize(v1, v0)
        else:
            dv = (v1 - v0)

        return -np.dot(self.H, dv)

    def map(self, v):
        """ return H*v """
        return -np.dot(self.H, v)

    def _build_dist(self, w_mat):
        """ generate R using distribution method. """
        lamb, p = self.params['lamb'], self.params['p']

        f = self.fwd.solve_eit(self.ex_mat, step=self.step, perm=self.perm,
                               parser=self.parser)
        jac = f.jac
        # E[yy^T], it is more efficient to use left pinv than right pinv
        j_j_w = np.dot(jac, jac.T)
        r_mat = np.diag(np.diag(j_j_w) ** p)
        jac_inv = la.inv(j_j_w + lamb*r_mat)
        # RM = E[xx^T] / E[yy^T]
        h_mat = np.dot(np.dot(w_mat.T, jac.T), jac_inv)

        return h_mat

    def _build_grid(self):
        """build grids and mask"""
        # initialize grids
        n = self.params['n']
        xg, yg, mask = meshgrid(self.pts, n=n)
        # mapping from values on triangles to values on grids
        xy = np.mean(self.pts[self.tri], axis=1)
        xyi = np.vstack((xg.flatten(), yg.flatten())).T
        # GREIT is using sigmod as weighting function (global)
        ratio, s = self.params['ratio'], self.params['s']
        w_mat = weight_sigmod(xy, xyi, ratio=ratio, s=s)
        return w_mat, xg, yg, mask

    def get_grid(self):
        """get grids and mask"""
        return self.xg, self.yg, self.mask

    def mask_value(self, ds, mask_value=0):
        """ (plot only) mask values on nodes outside 2D mesh. """
        ds[self.mask] = mask_value
        ds = ds.reshape(self.xg.shape)
        return self.xg, self.yg, ds

    @staticmethod
    def build_set(x, y):
        """ generate R from a set of training sets (deprecate). """
        # E_w[yy^T]
        y_y_t = la.inv(np.dot(y, y.transpose()))
        h_matrix = np.dot(np.dot(x, y), y_y_t)
        return h_matrix
