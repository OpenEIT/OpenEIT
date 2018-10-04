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
from .pyeit.eit.bp import BP as bp
from .pyeit.eit.fem import Forward

logger = logging.getLogger(__name__)


class BpReconstruction:

    """

    Reconstruction of image data from an EIT measurement.

    Using good old fashioned Back Projection. 

    """

    def __init__(self,n_el):
        # setup EIT scan conditions
        self.img = []
        self.baseline_flag = 0
        n_el = n_el # number of electrodes. 
        # el_dist is distance between send and receive electrode. 
        # dist is the distance (number of electrodes) of A to B
        # in 'adjacent' mode, dist=1, in 'apposition' mode, dist=ne/2        
        # el_dist, step = 1, 1
        el_dist, step = 1, 1


        try:

            # How should we write the electrode configuration, for the bipolar 8 electrode case? 
            # 0, 1, 2, 3 
            # Ben suggested how on github 
            # there was a pyeit example showing the combining of ex_mat arrangments. 
            # if step is 2 and we have 16 electrodes. How to make every second electrode 'transparent'. 

            # Firmware match: 
            if n_el == 32:
                # This is also the ordering of the voltages coming in at each measurement. 
                f = open('e_conf_'+str(n_el)+'.txt')
                triplets=f.read().split()
                for i in range(0,len(triplets)):
                    triplets[i]=triplets[i].split(',')
                A=np.array(triplets, dtype=np.uint8)
                self.ex_mat = np.unique(A[:,0:2],axis=0)
                logger.info("read electrode configuration")
                #print (self.ex_mat)
            else: 
                self.ex_mat = eit_scan_lines(n_el, el_dist)
                #print ('8 electrode option')
                #print (self.ex_mat)
        except RuntimeError as err:
            logger.error('e_conf file config error: %s', err)
            self.ex_mat = eit_scan_lines(n_el, el_dist)
            #print (self.ex_mat)

        """ 0. construct mesh """
        # h0 is initial mesh size. , h0=0.1
        self.mesh_obj, self.el_pos = mesh.create(n_el)
        
        # print("ex mat")
        # print (self.ex_mat)
        """ 3. Set Up BP """
        try: 
            self.eit =  bp(self.mesh_obj,  self.el_pos, ex_mat=self.ex_mat, step=step, parser='std')
            # parameter tuning is needed for better EIT images
            logger.info("BP mesh set up ")
        except RuntimeError as err:
            logger.error('e_conf file config error: %s', err)

        """ 3. Set Up default difference background """
        try: 
            if n_el == 32: 
                # load up the reference background data. 
                text_file = open("background_"+str(n_el)+".txt", "r")
                lines = text_file.readlines()
                self.f0 = self.parse_line(lines[1])
            else: # This is if electrode are 8 in length. 
                text_file = open("background_8.txt", "r")
                lines = text_file.readlines()
                self.f0 = self.parse_line(lines[1])
                # fwd = Forward(self.mesh_obj, self.el_pos) 
                # self.f0 = fwd.solve_eit(self.ex_mat, step=step, perm=self.mesh_obj['perm']).v
                #print ('f0 information: ')
                #print (self.f0.shape) # 40? 
                # print (self.f0) # why is this none? 
        except RuntimeError as err:
            logger.error('background file config error: %s', err)
            print ('creating the reference, this only works for 32 option')
            fwd = Forward(self.mesh_obj, self.el_pos) 
            self.f0 = fwd.solve_eit(self.ex_mat, step=step, perm=self.mesh_obj['perm']).v


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
        # self.f0 = data
        self.baseline_flag = 1
        # Write reference to file? 
        # filepath = 'background2.txt'
        # with open(filepath, 'w') as file_handler:
        #     file_handler.write("\nmagnitudes : ")
        #     for item in data:
        #         file_handler.write( (str(item)+',' ) )

    def reset_reference(self):
        """ reset the reference """
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
            self.f0 = fwd.solve_eit(self.ex_mat, step=step, perm=self.mesh_obj['perm']).v

    def eit_reconstruction(self, data):
        """
        Reconstruct an image from the measurements given by `data`.
        data is 928 long data that just came in. 

        # data is 40 in length? 
        # 

        """
        try: 
            #print ('size of info')

            # data contains fl.v and f0.v 
            f1 = np.array(data)
            #print (len(data))
            #print (self.f0.shape) # f0 is 928 in size. ?? // it's f0 that is wrong...
            #print (f1.shape)
            # if the jacobian is not normalized, data may not to be normalized too.
            ds_bp = self.eit.solve(f1, self.f0, normalize=False)
            self.img = np.real(ds_bp)

            if self.baseline_flag == 1 :
                    print ("baseline thing")
                    self.f0 = np.array(data)
                    self.baseline_flag = 0 

        except RuntimeError as err:
            logger.error('reconstruction problem: %s', err)

        return self.img
