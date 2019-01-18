"""

# Copyright (c) Mindseye Biomedical LLC. All rights reserved.
# Distributed under the (new) CC BY-NC-SA 4.0 License. See LICENSE.txt for more info.


This module contains an image reconstruction implementation of GREIT. 
Graz Consensus algorithm, shines on actual hardware. 

"""

import sys
import logging
import itertools
import time
import threading
import numpy as np
from .pyeit import mesh 
from .pyeit.eit.utils import eit_scan_lines
from .pyeit.eit.greit import GREIT as greit
from .pyeit.eit.fem import Forward

logger = logging.getLogger(__name__)


class GreitReconstruction:
    """

    Reconstruction of image data from an EIT measurement.
    Configurable wrapper to pyEIT 

    """
    def __init__(self,n_el):
        # setup EIT scan conditions
        self.img = []
        self.baseline_flag = 1
        self.n_el = n_el # number of electrodes. 
        self.el_dist = int(self.n_el/2) # random initialize number 
        self.step = 1
        # we create this according to an opposition protocol to maximize contrast. 
        self.ex_mat = eit_scan_lines(ne = self.n_el, dist = self.el_dist)
        """ 0. construct mesh """
        # h0 is initial mesh size. , h0=0.1
        self.mesh_obj, self.el_pos = mesh.create(self.n_el)
        """ 3. Set Up GREIT """
        self.eit = greit(self.mesh_obj, self.el_pos, ex_mat=self.ex_mat, step=self.step, parser='std')
        #self.eit.setup(p=0.50, lamb=0.5,n=self.n_el)
        self.eit.setup(p=0.50, lamb=0.05,n=self.n_el)
        logger.info("GREIT mesh set up ")
        self.gx = None
        self.gy = None
        self.ds = None

    def update_reference(self,data):
        # print (data)
        self.baseline_flag = 1

    def eit_reconstruction(self, data):
        """
        Reconstruct an image from the measurements given by `data`.

        """
        try: 
            if self.baseline_flag == 1: # if the baseline flag is on. 
                self.f0 = data
                self.baseline_flag = 0 
            f1 = np.array(data)
            self.ds = self.eit.solve(f1, self.f0,normalize=False)
            self.gx, self.gy, self.ds = self.eit.mask_value(self.ds, mask_value=np.NAN)
            self.img = np.real(self.ds)

        except RuntimeError as err:
            logger.info('reconstruction problem: %s', err)

        return self.img 