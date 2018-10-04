""" add customized plot for 2D/3D mesh """
from .voronoi_plot import voronoi_plot

try:
    from .tetplot import tetplot
except ImportError:
    print("mesh.plot: vispy is required for 3D plotting")

__all__ = ['voronoi_plot',
           'tetplot']
