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
from skimage.draw import line as ll
from skimage.transform import radon, iradon_sart


logger = logging.getLogger(__name__)



class RadonReconstruction:

    """
    Reconstruction of image data from an EIT measurement.

    The reconstruction works by interpolating the measurement data to
    create a sinogram and compute the image from this by inverse radon
    transformation.
    """

    def __init__(self):
        # problem, if I go down to say, 10, then some of the lines
        # aren't displayed.
        self.image_pixels = 100

        self.img = np.zeros((self.image_pixels, self.image_pixels),
                            dtype=np.float)

        # Above should be calculated elsewhere and is only for
        # plotting purposes.
        self.x_center = self.image_pixels/2
        self.y_center = self.image_pixels/2
        self.radius = self.image_pixels/2 - self.image_pixels/10
        #
        # Log file order, 8 choose 2.
        self.logfile = list(itertools.combinations(range(8), 2))
        # electrode points:
        self.theta_points = [np.pi, 5*np.pi/4, 3*np.pi/2, 7*np.pi/4,
                             0, np.pi/4, np.pi/2, 3*np.pi/4]

    def makeimages(self, data):
        if len(data) != len(self.logfile):
            raise ValueError(
                "the datasets must match the logfile specification"
            )

        # calculate the positions of the electrodes in the image space
        n1 = np.add(self.x_center*np.ones(len(self.theta_points)),
                    self.radius*np.cos(self.theta_points))
        n2 = np.add(self.y_center*np.ones(len(self.theta_points)),
                    self.radius*np.sin(self.theta_points))

        x = n1.astype(np.int)
        y = n2.astype(np.int)

        d = dict()
        for i, (point1, point2) in enumerate(self.logfile):

            # get the gradient angle theta
            g1 = x[point2] - x[point1]
            g2 = y[point2] - y[point1]
            angle = np.rad2deg(np.arctan2(g2, g1))

            if angle < 0:
                angle = angle + 180
            elif angle >= 180:
                angle = 0.0

            # get the line coordinates for the connection of the two
            # considered electrodes
            l_x, l_y = ll(x[point1], y[point1], x[point2], y[point2])

            # if we are close to an existing angle reuse this
            for a in d:
                if abs(a-angle) < 5:
                    d[a][l_x, l_y] += data[i]
                    break
            else:  # create a new array in this slot
                img = np.zeros((self.image_pixels, self.image_pixels),
                               dtype=np.float)
                img[l_x, l_y] = data[i]
                d[angle] = img

        deg = list(sorted(d))

        return d, deg

    def reconstruct(self, d, deg):
        interp_projections = []

        # now interpolate each angled projection, to get an
        # approximate radon transform from the EIT data
        for i, degi in enumerate(deg):
            projections = radon(d[degi], theta=deg, circle=True)
            p = projections[:, i]

            # problem is lines at angle, or indices next to each other
            # should just be one value..
            #
            # sift through p. if
            for t in range(len(p)):
                if p[t] > 0:
                    if p[t+1] > p[t]:
                        p[t] = 0
                    if p[t] < p[t-1] or p[t] < p[t-2]:
                        p[t] = 0

            nonzeroind = np.nonzero(p)[0]
            xp = nonzeroind
            yp = p[nonzeroind]

            xp = np.append([0], nonzeroind)
            yp = np.append(yp[0], yp)

            xp = np.append(xp, [len(p)-1])
            yp = np.append(yp, yp[-1])

            # Now interpolate to acquire the preimages for the inverse
            # radon transform
            xnew = np.linspace(0, len(p), len(p))
            yinterp = np.interp(xnew, xp, yp)
            interp_projections.append(yinterp)

        interp_projections = np.array(interp_projections).transpose()

        # reconstruction = iradon(interp_projections, theta=deg, circle=True)

        # SART reconstruction with two iterations for improved
        # accuracy
        reconstruction_sart = iradon_sart(interp_projections,
                                          theta=np.array(deg))
        reconstruction_sart2 = iradon_sart(interp_projections,
                                           theta=np.array(deg),
                                           image=reconstruction_sart)

        image = reconstruction_sart2
        return image

    def eit_reconstruction(self, data):
        """
        Reconstruct an image from the measurements given by `data`.
        """

        d, deg = self.makeimages(data)
        return self.reconstruct(d, deg)
