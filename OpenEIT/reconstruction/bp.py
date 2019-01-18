"""

# Copyright (c) Mindseye Biomedical LLC. All rights reserved.
# Distributed under the (new) CC BY-NC-SA 4.0 License. See LICENSE.txt for more info.


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
from .pyeit.eit.bp import BP as bp
from .pyeit.eit.fem import Forward

logger = logging.getLogger(__name__)


class BpReconstruction:

    """
    Reconstruction of image data from an EIT measurement.
    Using old fashioned Back Projection. 

    """
    def __init__(self,n_el):
        # setup EIT scan conditions
        self.img = []
        self.baseline_flag = 0
        self.n_el = n_el # number of electrodes. 
        self.step = 1 
        self.el_dist = int(self.n_el/2) # random initialize number 

        # we create this according to an opposition protocol to maximize contrast. 
        self.ex_mat = eit_scan_lines(ne = self.n_el, dist = self.el_dist)
        """ 0. construct mesh """
        # h0 is initial mesh size. , h0=0.1
        self.mesh_obj, self.el_pos = mesh.create(self.n_el)
        """ 3. Set Up BP """
        self.eit =  bp(self.mesh_obj,self.el_pos, ex_mat=self.ex_mat, step=self.step, parser='std')

        self.eit.setup(weight='none')

    def update_reference(self,data):
        self.baseline_flag = 1

    def eit_reconstruction(self, data):
        """
        Reconstruct an image from the measurements given by `data`.

        """
        try: 
            if self.baseline_flag == 1:
                self.f0 = np.array(data)
                self.baseline_flag = 0 
            # data contains fl.v and f0.v 
            f1 = np.array(data)
            # if the jacobian is not normalized, data may not to be normalized too.
            ds_bp = self.eit.solve(f1, self.f0, normalize=True)
            self.img = np.real(ds_bp)

        except RuntimeError as err:
            logger.error('reconstruction problem: %s', err)

        return self.img
