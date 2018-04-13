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
    def __init__(self):
        # setup EIT scan conditions
        self.img = []
        n_el = 32 # number of electrodes. 
        # el_dist is distance between send and receive electrode. 
        # dist is the distance (number of electrodes) of A to B
        # in 'adjacent' mode, dist=1, in 'apposition' mode, dist=ne/2        
        el_dist, step = 1, 1

        try:
            # Firmware match: 
            # This is also the ordering of the voltages coming in at each measurement. 
            f = open('e_conf.txt')
            triplets=f.read().split()
            for i in range(0,len(triplets)):
                triplets[i]=triplets[i].split(',')
            A=np.array(triplets, dtype=np.uint8)
            # subarray = A[:,0:2]
            self.ex_mat = np.unique(A[:,0:2],axis=0)
            logger.info("read electrode configuration")
        except RuntimeError as err:
            logger.error('e_conf file config error: %s', err)
            self.ex_mat = eit_scan_lines(n_el, el_dist)

        """ 0. construct mesh """
        # h0 is initial mesh size. , h0=0.1
        self.mesh_obj, self.el_pos = mesh.create(n_el)

        """ 3. Set Up JAC """
        try: 
            self.eit = jac(self.mesh_obj,  self.el_pos, ex_mat=self.ex_mat, step=step, perm=1., parser='std')
            # parameter tuning is needed for better EIT images
            self.eit.setup(p=0.5, lamb=0.1, method='kotre')

            logger.info("JAC mesh set up ")
            print ('set up greit mesh')
        except RuntimeError as err:
            logger.error('e_conf file config error: %s', err)

        """ 3. Set Up default difference background """
        try: 
            # load up the reference background data. 
            text_file = open("background.txt", "r")
            lines = text_file.readlines()
            self.f0 = self.parse_line(lines[1])
            print ('loaded background reference')
            print (type(self.f0))
            # print (self.f0) # why is this none? 
        except RuntimeError as err:
            logger.error('background file config error: %s', err)
            print ('creating the reference')
            fwd = Forward(self.mesh_obj, self.el_pos) 
            self.f0 = fwd.solve_eit(self.ex_mat, step=step, perm=self.mesh_obj['perm'])
            print (len(self.f0))


        self.pts = self.mesh_obj['node']
        self.tri = self.mesh_obj['element']
        # self.x,self.y = self.pts[:, 0], pts[:, 1]

    def parse_line(self,line):
        try:
            _, data = line.split(":", 1)
        except ValueError:
            return None

        items = []
        for item in data.split(","):
            item = item.strip()
            if not item:
                continue
            try:
                items.append(float(item))
            except ValueError:
                return None
        return np.array(items)

    def update_reference(self,data):
        self.f0 = data
        # Write reference to file? 
        # filepath = 'background.txt'
        # with open(filepath, 'w') as file_handler:
        #     file_handler.write("\nmagnitudes : ")
        #     for item in info:
        #         file_handler.write( (str(item)+',' ) )

    def reset_reference(self):
        try: 
            # load up the reference background data. 
            text_file = open("background.txt", "r")
            lines = text_file.readlines()
            self.f0 = self.parse_line(lines[1])
            print ('loaded default reference')
        except RuntimeError as err:
            logger.error('background file config error: %s', err)
            print ('resetting the reference')
            fwd = Forward(self.mesh_obj, self.el_pos) 
            self.f0 = fwd.solve_eit(self.ex_mat, step=step, perm=self.mesh_obj['perm'])

    def eit_reconstruction(self, data):
        """
        Reconstruct an image from the measurements given by `data`.
        data is 928 long data that just came in. 

        """
        try: 
            # data contains fl.v and f0.v 
            f1 = np.array(data)
            # if the jacobian is not normalized, data may not to be normalized too.
            ds = self.eit.solve(f1, self.f0,normalize=False)
            ds_jac = sim2pts(self.pts, self.tri, ds)
            self.img = np.real(ds_jac)

        except RuntimeError as err:
            logger.error('reconstruction problem: %s', err)

        return self.img