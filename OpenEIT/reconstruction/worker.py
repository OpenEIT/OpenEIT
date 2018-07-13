"""
This module contains an image reconstruction implementation based
on interpolation and inverse radon transformation.
"""

import logging
import itertools
import time
import threading
import numpy as np

from .bp import BpReconstruction
from .jac import JacReconstruction
from .greit import GreitReconstruction
from .radon import RadonReconstruction

logger = logging.getLogger(__name__)


class ReconstructionWorker(threading.Thread):
    """
    A reconstruction worker thread.

    When running it takes measurement data (as sequence of impedance
    measurements) from `input_queue`, reconstructs the image data and
    puts the reconstructed image to `output_queue`.
    """

    def __init__(self, input_queue, output_queue,algorithm,n_el):
        super().__init__(daemon=True)
        self._input_queue   = input_queue
        self._output_queue  = output_queue
        self._running       = True
        self._algorithm     = algorithm

        if self._algorithm == 'bp':
            self._reconstruction = BpReconstruction(n_el)
        elif self._algorithm  == 'greit':
            self._reconstruction = GreitReconstruction(n_el)
        elif self._algorithm  == 'jac':
            self._reconstruction = JacReconstruction(n_el)
        else: # radon transform here is for 8 electrodes only. 
            self._reconstruction = RadonReconstruction()

    def baseline(self):
        data = np.array(self._input_queue.get())
        self._reconstruction.update_reference(data)

    def reset_baseline(self):
        self._reconstruction.reset_reference()

    def get_plot_params(self):
        mesh_obj = self._reconstruction.mesh_obj
        pts = mesh_obj['node']
        tri = mesh_obj['element']
        x= pts[:, 0]
        y = pts[:, 1]
        el_pos = self._reconstruction.el_pos
        return x,y,tri,el_pos


    def get_greit_params(self):
        return self._reconstruction.gx,self._reconstruction.gy,self._reconstruction.ds

    def get_radon_params(self):
        return 0

    def stop(self):
        self._running = False

    def run(self):
        # TODO: add time tracking here!
        while self._running:
            data = np.array(self._input_queue.get())
            # 
            # this is going to be 928 long data pipe. 
            # 
            # preprocess the data to exclude zero values? 
            data = [1.0 if x == 0 else x for x in data]
            try:
                before = time.time()
                img = self._reconstruction.eit_reconstruction(data)
                logger.info("reconstruction time: %.2f", time.time() - before)
            except RuntimeError as err:
                logger.error('reconstruction error: %s', err)
            else:
                self._output_queue.put(img)

