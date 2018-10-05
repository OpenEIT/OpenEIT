from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
print (__version__) # requires version >= 1.9.0
import plotly as py
# py.tools.set_credentials_file(username='jeantoul', api_key='CSg2CWv44LpZjFwrotL2')
# from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
# jeantoul
# horribleporridge
# API KEY: CSg2CWv44LpZjFwrotL2
# Streaming API Key: 3t1bnuje1q
import plotly.figure_factory as FF
import plotly.graph_objs as go
import numpy as np
from scipy.spatial import Delaunay
from plotly.tools import FigureFactory as ff
import matplotlib.pyplot as plt
import matplotlib.tri as tri
import numpy as np

# u=np.linspace(-np.pi/2, np.pi/2, 60)
# v=np.linspace(0, np.pi, 60)
# u,v=np.meshgrid(u,v)
# u=u.flatten()
# v=v.flatten()

# x = (np.sqrt(2)*(np.cos(v)*np.cos(v))*np.cos(2*u) + np.cos(u)*np.sin(2*v))/(2 - np.sqrt(2)*np.sin(3*u)*np.sin(2*v))
# y = (np.sqrt(2)*(np.cos(v)*np.cos(v))*np.sin(2*u) - np.sin(u)*np.sin(2*v))/(2 - np.sqrt(2)*np.sin(3*u)*np.sin(2*v))
# z = (3*(np.cos(v)*np.cos(v)))/(2 - np.sqrt(2)*np.sin(3*u)*np.sin(2*v))

# points2D = np.vstack([u, v]).T
# tri = Delaunay(points2D)
# simplices = tri.simplices

# First create the x and y coordinates of the points.
n_angles = 36
n_radii = 8
min_radius = 0.25
radii = np.linspace(min_radius, 0.95, n_radii)

angles = np.linspace(0, 2 * np.pi, n_angles, endpoint=False)
angles = np.repeat(angles[..., np.newaxis], n_radii, axis=1)
angles[:, 1::2] += np.pi / n_angles

x = (radii * np.cos(angles)).flatten()
y = (radii * np.sin(angles)).flatten()
z = (np.cos(radii) * np.cos(3 * angles)).flatten()

# Create the Triangulation; no triangles so Delaunay triangulation created.
triang = tri.Triangulation(x, y)

# Mask off unwanted triangles.
triang.set_mask(np.hypot(x[triang.triangles].mean(axis=1),
                         y[triang.triangles].mean(axis=1))
                < min_radius)
# self.topplot = self.topimageplt.tripcolor(self.x,self.y, self.tri, self.img,
#      shading='flat', alpha=0.90, cmap=plt.cm.viridis,vmin=self.min_cbar,vmax=self.max_cbar)

# triang, z, shading='flat'

fig1 = FF.create_trisurf(x=x, y=y, z=z,
                         colormap=['rgb(50, 0, 75)', 'rgb(200, 0, 200)', '#c8dcc8'],
                         show_colorbar=True,
                         simplices=triang,
                         title="Boy's Surface")        

# fig1 = FF.create_trisurf(x=x, y=y, z=z,
#                          colormap=['rgb(50, 0, 75)', 'rgb(200, 0, 200)', '#c8dcc8'],
#                          show_colorbar=True,
#                          simplices=simplices,
#                          title="Boy's Surface")

plot(fig1, filename="figs")

# import plotly.graph_objs as go

# plot([go.Scatter(x=[1, 2, 3], y=[3, 1, 6])])