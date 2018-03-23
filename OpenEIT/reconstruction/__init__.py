"""
Reconstruction of image data from raw data.
"""

# TODO: define reconstruction algorithm independent device
# configurations, some reconstruction algorithms may choose to ignore
# some of that information, this way the number of electrodes and
# so on can be set as a free parameter!

# TODO: define an abstract interface for reconstruction algorithms.

from .radon import ReconstructionWorker
