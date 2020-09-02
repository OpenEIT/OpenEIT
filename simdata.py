"""
    Simdata: simulates the firmware, outputting data in the same format. 

	Example set up of GREIT algorithm. 
	This also creates fake data to feed in, for testing purposes. 

	If you want to experiment with running algorithms outside the dashboard, this is currently a messy yet functional template. 

	Note: In current form this only works with tetrapolar electrode configurations. 
	You will need the correct e_conf for it to work. 

"""

import matplotlib
matplotlib.use("TkAgg")
import numpy as np
import matplotlib.pyplot as plt
import math
import OpenEIT.dashboard
import OpenEIT.reconstruction 


""" GREIT calls """
# initialize all parameters. 
g = OpenEIT.reconstruction.GreitReconstruction(n_el=32)

# variables needed to set up the forward simulation of data. 
mesh_obj = g.mesh_obj
el_pos = g.el_pos
ex_mat = g.ex_mat
step = 1
radius = 0.6
numberofmeasures = 10
# array, node, perm. 

""" 1. problem setup """
def PointsInCircum(r,n=100):
    return [[math.cos(2*math.pi/n*x)*r,math.sin(2*math.pi/n*x)*r] for x in range(0,n+1)]

circlepts = np.array(PointsInCircum(radius,n=numberofmeasures))
length,nos = circlepts.shape # 101 by 2 

# print ('starting for loop')


for i in range(length):
	print (i)
	xval = circlepts[i,0] 
	yval = circlepts[i,1]
	anomaly = [{'x': xval,  'y': 0,    'd': 0.1, 'perm': 10},
	           {'x': -xval, 'y': 0,    'd': 0.1, 'perm': 10},
	           {'x': 0,    'y': yval,  'd': 0.1, 'perm': 0.1},
	           {'x': 0,    'y': -yval, 'd': 0.1, 'perm': 0.1}]
	mesh_new = OpenEIT.reconstruction.mesh.set_perm(mesh_obj, anomaly=anomaly, background=1.0)
	

	# delta_perm = np.real(mesh_new['perm'] - mesh_obj['perm'])
	# # 
	# perm = mesh_obj['perm']
	# #show alpha
	# fig, ax = plt.subplots(figsize=(6, 4))
	# im = ax.tripcolor(pts[:, 0], pts[:, 1], tri, delta_perm,
	#                   shading='flat', cmap=plt.cm.viridis)
	# fig.colorbar(im)
	# ax.axis('equal')
	# ax.set_xlim([-1.2, 1.2])
	# ax.set_ylim([-1.2, 1.2])
	# ax.set_title(r'$\Delta$ Conductivity')
	# fig.set_size_inches(6, 4)
	# ax.show()

	""" 2. FEM forward simulations """
	# calculate simulated data
	fwd = OpenEIT.reconstruction.Forward(mesh_obj, el_pos)
	# f0 = fwd.solve_eit(ex_mat, step=step, perm=mesh_obj['perm'])
	f1 = fwd.solve_eit(ex_mat, step=step, perm=mesh_new['perm'])

	# g.update_reference(f0.v)
	# data must be appropriately formatted, then send to image reconstruction. 
	# data = f1.v.tolist()

	info = f1.v

	print (len(info))

	filepath = 'simdata.txt'
	with open(filepath, 'a') as file_handler:
	    file_handler.write("\nmagnitudes : ")
	    for item in info:
	        file_handler.write( (str(item)+',' ) )
 
# filepath = 'gbackground.txt'
# with open(filepath, 'w') as file_handler:
#     file_handler.write("\nmagnitudes : ")
#     for item in info:
#         file_handler.write( (str(item)+',' ) )



