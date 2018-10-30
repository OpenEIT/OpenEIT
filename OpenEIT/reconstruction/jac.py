"""
This module contains an image reconstruction implementation based
on interpolation and inverse radon transformation.
"""

import logging
import itertools
import time
import threading

import numpy as np
from .pyeit import mesh 
from .pyeit.eit.utils import eit_scan_lines
from .pyeit.eit.jac import JAC as jac
from .pyeit.eit.fem import Forward
from .pyeit.eit.interp2d import sim2pts

logger = logging.getLogger(__name__)


class JacReconstruction:
    """

    Reconstruction of image data from an EIT measurement.
    Configurable wrapper to pyEIT 

    """
    def __init__(self,n_el):
        # setup EIT scan conditions
        self.img = []
        self.baseline_flag = 1
        self.n_el = n_el # number of electrodes. 
        self.n_el = n_el # number of electrodes. 
        # self.step = int(self.n_el/2) # random initialize number 
        # self.el_dist = self.step
        #
        # This makes for a different number of points. 192 not 224... 
        self.el_dist = int(self.n_el/2)
        self.step = 1 # 
        # 
        # we create this according to an opposition protocol to maximize contrast. 
        self.ex_mat = eit_scan_lines(ne = self.n_el, dist = self.el_dist)

        """ 0. construct mesh """
        # h0 is initial mesh size. , h0=0.1
        self.mesh_obj, self.el_pos = mesh.create(n_el)
        """ 3. Set Up JAC """
        self.eit = jac(self.mesh_obj, self.el_pos, ex_mat=self.ex_mat, step=self.step, perm=1., parser='std')
        # parameter tuning is needed for better EIT images
        self.eit.setup(p=0.5, lamb=0.5, method='kotre')
        logger.info("JAC mesh set up ")
        self.ds  = None
        self.pts = self.mesh_obj['node']
        self.tri = self.mesh_obj['element']

    def update_reference(self,data):
        self.baseline_flag = 1

    def eit_reconstruction(self, data):
        """
        Reconstruct an image from the measurements given by `data`.
        data is 928 long data that just came in. 

        """
        try: 
            if self.baseline_flag == 1: 
                self.f0 = data
                self.baseline_flag = 0 
            # data contains fl.v and f0.v 
            f1 = np.array(data)
            # if the jacobian is not normalized, data may not to be normalized also.
            self.ds = self.eit.solve(f1, self.f0, normalize=False)
            ds_jac  = sim2pts(self.pts, self.tri, self.ds)
            self.img = np.real(ds_jac)

        except RuntimeError as err:
            logger.error('reconstruction problem: %s', err)

        return self.img