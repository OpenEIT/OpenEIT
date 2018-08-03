"""
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
        n_el = n_el # number of electrodes. 
        # el_dist is distance between send and receive electrode. 
        # dist is the distance (number of electrodes) of A to B
        # in 'adjacent' mode, dist=1, in 'apposition' mode, dist=ne/2        
        el_dist, step = 1, 1
        
        try:
            # Firmware match: 
            # This is also the ordering of the voltages coming in at each measurement. 
            f = open('e_conf_'+str(n_el)+'.txt')
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

        """ 3. Set Up GREIT """

        self.eit = greit(self.mesh_obj,  self.el_pos, ex_mat=self.ex_mat, step=step, parser='std')
        self.eit.setup(p=0.50, lamb=0.001,n=n_el)
        logger.info("GREIT mesh set up ")
        print ('set up greit mesh')

        """ 3. Set Up default difference background """
        try: 
            # load up the reference background data. 
            text_file = open("background_"+str(n_el)+".txt", "r")
            lines = text_file.readlines()
            self.f0 = self.parse_line(lines[1])
            print ('loaded background reference')

            # print (self.f0) # why is this none? 
        except RuntimeError as err:
            logger.error('background file config error: %s', err)
            print ('creating the reference')
            # test function for altering the permittivity in mesh

        """
            Initialize gx and gy.  
        """
        fwd = Forward(self.mesh_obj, self.el_pos) 
        
        # f0 = fwd.solve_eit(self.ex_mat, step=step, perm=self.mesh_obj['perm'])
        anomaly = [{'x': 0.4, 'y': 0.4, 'd': 0.2, 'perm': 100}]
        mesh_new = mesh.set_perm(self.mesh_obj, anomaly=anomaly, background=1.)
        f1 = fwd.solve_eit(self.ex_mat, step=step, perm=mesh_new['perm'])

        ds = self.eit.solve(f1.v, self.f0 , normalize=False)
        self.gx, self.gy, self.ds = self.eit.mask_value(ds, mask_value=np.NAN)



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
        # print (data)
        self.baseline_flag = 1
        # self.f0 = data
        # Write reference to file?
        # filepath = 'background.txt'
        # with open(filepath, 'w') as file_handler:
        #     file_handler.write("\nmagnitudes : ")
        #     for item in info:
        #         file_handler.write( (str(item)+',' ) )

    def reset_reference(self):
        """ reset the reference """
        try: 
            # load up the reference background data. 
            text_file = open("background_"+str(n_el)+".txt", "r")
            lines = text_file.readlines()
            self.f0 = self.parse_line(lines[1])

            print ('loaded default reference')
            # print (self.f0)
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
            ds = self.eit.solve(f1, self.f0,normalize=False)
            gx, gy, ds = self.eit.mask_value(ds, mask_value=np.NAN)
            self.img = np.real(ds)
            if self.baseline_flag == 1:
                self.f0 = data
                self.baseline_flag = 0 

        except RuntimeError as err:
            logger.info('reconstruction problem: %s', err)

        return self.img # ready to plot 32,32 image. 