"""

# Copyright (c) Mindseye Biomedical LLC. All rights reserved.
# Distributed under the (new) CC BY-NC-SA 4.0 License. See LICENSE.txt for more info.

	Read in a data file and plot it using an algorithm. 

"""
from __future__ import division, absolute_import, print_function
import numpy as np
import matplotlib.pyplot as plt
import OpenEIT.dashboard
import OpenEIT.reconstruction 

def parse_line(line):
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

n_el = 32
""" Load Data: select a file you have created by simdata.py, or recorded through the dashboard """
text_file = open("rawdata8.txt", "r")
lines       = text_file.readlines()
print ("length lines: ",len(lines))
# This is the baseline image.
f0          = parse_line(lines[4]).tolist()
# this is the new difference image. 
f1          = parse_line(lines[5]).tolist()

""" Select one of the three methods of EIT tomographic reconstruction, Gauss-Newton(Jacobian), GREIT, or Back Projection(BP)"""
# This is the Gauss Newton Method for tomographic reconstruction. 
g = OpenEIT.reconstruction.JacReconstruction(n_el=n_el)
# Note: Greit method uses a different mesh, so the plot code will be different.
# g = OpenEIT.reconstruction.GreitReconstruction(n_el=n_el)
# 
#g = OpenEIT.reconstruction.BpReconstruction(n_el=n_el)

data_baseline = f0
print ('f0',len(f0),len(f1))
g.update_reference(data_baseline)
# set the baseline. 
baseline = g.eit_reconstruction(f0)
# do the reconstruction. 
difference_image = g.eit_reconstruction(f1)
#print (difference_image)
# #print(g.__dict__)


mesh_obj = g.mesh_obj
el_pos = g.el_pos
ex_mat = g.ex_mat
pts     = g.mesh_obj['node']
tri = g.mesh_obj['element']
x   = pts[:, 0]
y   = pts[:, 1]

""" Uncomment the below code if you wish to plot the Jacobian(Gauss-Newton) or Back Projection output. Also, please look at the pyEIT documentation on how to optimize and tune the algorithms. A little tuning goes a long way! """
# JAC OR BP RECONSTRUCTION SHOW # 
fig, ax = plt.subplots(figsize=(6, 4))
im = ax.tripcolor(x,y, tri, difference_image,
                  shading='flat', cmap=plt.cm.gnuplot)
ax.plot(x[el_pos], y[el_pos], 'ro')
for i, e in enumerate(el_pos):
    ax.text(x[e], y[e], str(i+1), size=12)
ax.axis('equal')
fig.colorbar(im)
plt.show()


""" Uncomment the below code if you wish to plot the GREIT output. Also, please look at the pyEIT documentation on how to optimize and tune the algorithms. A little tuning goes a long way! """
# GREIT RECONSTRUCION IMAGE SHOW # 
# new     = difference_image[np.logical_not(np.isnan(difference_image))]
# flat    = new.flatten()
# av      = np.median(flat)
# total   = []
# for i in range(32):
#     for j in range(32):
#         if difference_image[i,j] < -5000: 
#             difference_image[i,j] = av

# print ('image shape: ',difference_image.shape)
# fig, ax = plt.subplots(figsize=(6, 4))
# #rotated = np.rot90(image, 1)
# im = ax.imshow(difference_image, interpolation='none', cmap=plt.cm.rainbow)
# fig.colorbar(im)
# ax.axis('equal')
# ax.set_title(r'$\Delta$ Conductivity Map of Lungs')
# fig.set_size_inches(6, 4)
# # fig.savefig('../figs/demo_greit.png', dpi=96)
# plt.show()


