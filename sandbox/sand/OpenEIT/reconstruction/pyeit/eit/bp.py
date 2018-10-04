# coding: utf-8
# pylint: disable=invalid-name, no-member, arguments-differ
""" bp (back-projection) and f(filtered)-bp module """
# Copyright (c) Benyuan Liu. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
from __future__ import division, absolute_import, print_function

import numpy as np
from .base import EitBase


class BP(EitBase):
    """ implement a naive inversion of (Euclidean) back projection. """

    def setup(self, weight='none'):
        """ setup BP """
        self.params = {
            "weight": weight
        }

        # build the weighting matrix
        if weight == 'simple':
            weights = self.simple_weight(self.B.shape[0])
            self.H = weights * self.B

    def solve(self, v1, v0=None, normalize=True):
        """
        back projection : mapping boundary data on element
        (note) normalize method affect the shape (resolution) of bp

        Parameters
        ----------
        v1 : NDArray
        v0 : NDArray, optional
            d = H(v1 - v0)
        normalize : Boolean
            true for conducting normalization

        Returns
        -------
        NDArray
            real-valued NDArray, changes of conductivities
        """
        # without specifying any reference frame
        if v0 is None:
            v0 = self.v0
        # choose normalize method, we use sign by default
        if normalize:
            vn = -(v1 - v0) / np.sign(self.v0)
        else:
            vn = (v1 - v0)
        # print (' v and H shapes ')
        # # How tid v get to be this shape? 
        # print (vn.shape)
        # print (v1.shape)
        # print(v0.shape) # 28... 
        # print (self.H.shape) # this one is 40 x 361? 
        # smearing
        ds = np.dot(self.H.transpose(), vn)
        return np.real(ds)

    def map(self, v):
        """ return Hx """
        x = -v / np.sign(self.v0)
        return np.dot(self.H.transpose(), x)

    def solve_gs(self, v1, v0):
        """ solving using gram-schmidt """
        a = np.dot(v1, v0) / np.dot(v0, v0)
        vn = - (v1 - a*v0) / np.sign(self.v0)
        ds = np.dot(self.H.transpose(), vn)
        return ds

    def simple_weight(self, num_voltages):
        """
        building weighting matrix : simple, normalize by radius.

        Note
        ----
        as in fem.py, we could either smear at
        (1) elements, using the center co-ordinates (x,y) of each element
            >> center_e = np.mean(self.pts[self.tri], axis=1)
        (2) nodes.

        Parameters
        ----------
        num_voltages : int
            number of equal-potential lines

        Returns
        -------
        NDArray
            weighting matrix
        """
        d = np.sqrt(np.sum(self.pts ** 2, axis=1))
        r = np.max(d)
        w = (1.01*r - d) / (1.01*r)
        # weighting by element-wise multiplication W with B
        weights = np.dot(np.ones((num_voltages, 1)), w.reshape(1, -1))
        return weights
