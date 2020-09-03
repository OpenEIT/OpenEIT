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

    def __init__(self):
        super().__init__(daemon=True)

        self._input_queue = None
        self._output_queue = None
        self._reconstruction = None
        self._running = True
        self._algorithm = None

    def reset(self,input_queue, output_queue,algorithm,n_el):
        self._input_queue   = None
        self._output_queue  = None
        #self._reconstruction = None

        self._input_queue   = input_queue
        self._output_queue  = output_queue
        self._running       = True
        self._algorithm     = algorithm
        self._baseline      = 1 

        if self._algorithm == 'bp':
            self._reconstruction = BpReconstruction(n_el)
        elif self._algorithm  == 'greit':
            self._reconstruction = GreitReconstruction(n_el)
        elif 'jac' in self._algorithm:
            # resetting for new number of electrodes. 
            self._reconstruction = JacReconstruction(n_el)
            self._reconstruction.reset(n_el)

    def baseline(self):
        self._baseline = 1

    def reset_baseline(self):
        self._reconstruction.reset_reference()

    def get_plot_params(self):
        mesh_obj = self._reconstruction.mesh_obj
        pts = mesh_obj['node']
        tri = mesh_obj['element']
        x = pts[:, 0]
        y = pts[:, 1]
        el_pos = self._reconstruction.el_pos
        return x,y,tri,el_pos

    def get_greit_params(self):
        return self._reconstruction.gx,self._reconstruction.gy,self._reconstruction.ds

    def get_radon_params(self):
        return 0

    def stop_reconstructing(self):
        self._running = False

    def start_reconstructing(self):
        self._running = True

    def run(self):
        # TODO: add time tracking here!
        while self._running:
            if self._input_queue is not None:             
                data = np.array(self._input_queue.get())
                # preprocess the data to exclude zero values? 
                data = [1.0 if x == 0 else x for x in data]

                if len(data) > 1:

                    if self._baseline == 1: 
                        self._reconstruction.update_reference(data)
                        self._baseline = 0

                    try:
                        before = time.time()
                        img = self._reconstruction.eit_reconstruction(data)
                        logger.info("reconstruction time: %.2f", time.time() - before)
                    except RuntimeError as err:
                        logger.info('reconstruction error: %s', err)
                    else:
                        self._output_queue.put(img)
                else: 
                    print ('forcing stop reconstruct')
                    self._running = False

