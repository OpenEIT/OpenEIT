"""

1. Simulate the image, determine the ideal sinogram for it. - Done. 
2. Then re-create the image from the data, and create a sinogram from it. 
3. Compare 1 and 2. Error lies here. 

"""
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt

import scipy.misc
import numpy as np
import imageio
from skimage.draw import line as ll
from skimage.draw import (line_aa, circle,
                          circle_perimeter_aa)
from skimage.draw import line, set_color
from skimage.viewer import ImageViewer
from matplotlib import cm
# from skimage.io import imread
from skimage import data_dir
from skimage.transform import radon, iradon
from scipy.ndimage import zoom
from skimage.transform import iradon_sart

#fname = "datasets/big_glass.log"
#fname = "datasets/shotglass2.log"
#fname = "datasets/shotglass3.log"
#fname = "datasets/twoobjects.log"
#fname = "datasets/shotglasshorizontalandrotated.log"
#fname = "datasets/shotglassanticlockwise.log"
fname = "datasets/Nothing.log"

ss = fname.split("/")[1][0:-4]

imagearray = []
n 		= 0
lines 	= []
with open(fname, "r") as f:
	for l in f:
		if "magnitudes" in l:

			if len(l) >= 200: #438:
				#	print 'here'
				# remove the letters, commas and convert to floats. 
				datastring = l.rstrip().replace(" ","").split(':')[1].split(',')
				#print datastring
				data = map(float, datastring[:-1]) # remove the trailing element after the comma. 
				lines.append(data)
				n=n+1	
	
print 'lines of data:',len(lines)	
logfile = [12,13,14,15,16,17,18,23,24,25,26,27,28,34,35,36,37,38,45,46,47,48,56,57,58,67,68,78]	
# two objects
t2 = [0.1,1,1,0.1,1,1,0.1,0.1,1,0.5,1,1,0.1,1,1,1,1,0.1,0.1,0.1,1,0.1,0.1,1,0.1,1,1,0.1]	
# middle object
t1 = [0.1,0.2,1,1,1,0.2,0.1,0.1,0.5,1,1,1,0.1,0.1,1,1,1,1,0.1,0.8,1,1,0.1,0.1,1,0.1,0.1,0.1]	


	
"""
2. 
"""
image_pixels 		= 100 # problem, if I go down to say, 10, then some of the lines aren't displayed. 
minimal_value_fbp 	= 0
maximal_value_fbp 	= 40000
minimal_value_sart 	= 0
maximal_value_sart 	= 40000
inter_min			= 0
inter_max			= 100000
# then find all the 8 points where electrodes are. 
x_center 			= image_pixels/2
y_center 			= image_pixels/2
radius 	 			= image_pixels/2 - image_pixels/10
# this is our series of coordinates to create lines from. 
r,c,val 			= circle_perimeter_aa(x_center, y_center, radius)
# img[r, c] = val * 255

# electrode points: 
theta_points=[np.pi,5*np.pi/4,3*np.pi/2,7*np.pi/4,0,np.pi/4,np.pi/2,3*np.pi/4]
n1 = np.add(x_center*np.ones(len(theta_points)) , radius*np.cos(theta_points)) #  shift center
n2 = np.add(y_center*np.ones(len(theta_points)) , radius*np.sin(theta_points)) #
x = []
y = []
for i in xrange(len(n1)):
	x.append(int(n1[i]))
	y.append(int(n2[i]))

firstreconstruction = []
for j in xrange(len(lines)-1): # len(lines)-1

	data = lines[j] # t1 #test_data #lines[2]
	d = dict()

	# 8 choose 2
	for i in xrange(28):
		number = str(logfile[i])
		point1,point2 = int(number[0])-1, int(number[1])-1
		# Get the gradient angle theta. 
		g1 = (x[point2] - x[point1])
		g2 = (y[point2]- y[point1])
		angle = (np.rad2deg(np.arctan2(g2, g1)))
		if angle<0:
			angle= angle+180
		if angle >= 180:
			angle = 0
		# print angle
		# get the line coords by parsing logfile identity order string
		l_x, l_y = ll(x[point1], y[point1], x[point2], y[point2])
		# check if angle is not close to any of the existing angles. 
		mark = 0 
		img = np.zeros((image_pixels, image_pixels), dtype=np.float)
		for a in d: 
			if abs(a-(angle))<5:
				# print a, angle
				img 			= d[a]
				img[l_x, l_y] 	= img[l_x, l_y]+data[i]
				# build up the image for each angle. 
				d[a]=img
				mark = 1
		if mark == 0: # if it doesn't already exist. 
			# print angle
			img[l_x, l_y] = data[i]
			#print data[i]
			# create a new array in this slot
			d[angle] = img
		  
	# 
	deg = []
	for key in d:
		deg.append(key)
	keyz = deg
	# 
	# print len(keyz)
	# print keyz
	# 
	# np.savez('out.npz',deg,d)
	# npzfile = np.load('dataFile.npz')
	# fig, ((ax1,ax2,ax3,ax4),(ax5,ax6,ax7,ax8)) = plt.subplots(2,4, sharex='col', sharey='row',figsize=(8,4))
	# a = ax1.imshow(d[keyz[0]], interpolation='nearest', cmap=cm.coolwarm, aspect='auto')
	# fig.colorbar(a, ax=ax1, cax=ax1)
	# ax2.imshow(d[keyz[1]], interpolation='nearest', cmap=cm.coolwarm, aspect='auto')
	# ax3.imshow(d[keyz[2]], interpolation='nearest', cmap=cm.coolwarm, aspect='auto')
	# ax4.imshow(d[keyz[3]], interpolation='nearest', cmap=cm.coolwarm, aspect='auto')
	# ax5.imshow(d[keyz[4]], interpolation='nearest', cmap=cm.coolwarm, aspect='auto')
	# ax6.imshow(d[keyz[5]], interpolation='nearest', cmap=cm.coolwarm, aspect='auto')
	# ax7.imshow(d[keyz[6]], interpolation='nearest', cmap=cm.coolwarm, aspect='auto')
	# ax8.imshow(d[keyz[7]], interpolation='nearest', cmap=cm.coolwarm, aspect='auto')		
	# plt.show()
	# 
	interp_projections = []
	# Now interpolate for each angled projection, and place back into the projection. 
	for i in xrange(len(deg)):
		# print 'degrees: ',deg[i],d[deg[i]].shape, deg
		# sinogram = radon(image, theta=theta, circle=True)
		projections = radon(d[deg[i]], theta=deg, circle= True)

		# print 'projections shape',projections.shape
		p = projections[:,i]
		# 
		# problem is lines at angle, or indices next to each other should just be one value..
		# 
		# sift through p. if 
		for t in xrange(len(p)):
			if p[t]>0:
				if p[t+1]>p[t]:
					p[t]=0
				if p[t]<p[t-1] or p[t]<p[t-2]:
					p[t]=0
		# plt.figure()
		# plt.plot(p,'.')
		# plt.show()
		nonzeroind = np.nonzero(p)[0] 
		# print 'nonzeros', len(nonzeroind), p.shape
		# what happened?
		xp = nonzeroind
		yp = p[nonzeroind]
		# add the beginning part. 
		xp = np.append([0],nonzeroind)
		yp = np.append(yp[0],yp)
		# add the end part
		xp = np.append(xp,[len(p)-1])
		yp = np.append(yp,yp[-1])
		
		# print type(yp),type(xp)
		#print xp, yp
		# Now interpolate to acquire 
		xnew = np.linspace(0, len(p),len(p))
		# print len(xnew)
		yinterp = np.interp(xnew, xp, yp)
		interp_projections.append(yinterp)

	interp_projections = np.array(interp_projections).transpose()

	reconstruction = iradon(interp_projections, theta=deg, circle=True)
	# SART reconstruction: 
	reconstruction_sart = iradon_sart(interp_projections, theta=np.array(deg))
	reconstruction_sart2 = iradon_sart(interp_projections, theta=np.array(deg),
                                   image=reconstruction_sart)

	rad = reconstruction_sart2
	if j == 0:
		# med = np.median(reconstruction)
		# std = 3*np.std(reconstruction)
		inter_min 			= interp_projections.min()
		inter_max 			= interp_projections.max()
		minimal_value_fbp 	= reconstruction.min()
		maximal_value_fbp 	= reconstruction.max()
		minimal_value_sart 	= reconstruction_sart2.min()
		maximal_value_sart 	= reconstruction_sart2.max()
	  	firstreconstruction = reconstruction_sart2
	else: 
		rad = reconstruction_sart2 - firstreconstruction

	fig = plt.figure(figsize=(8, 8.5))
	canvas = FigureCanvas(fig)
	plt.subplot(221)
	plt.title("Sinogram");
	plt.imshow(interp_projections, cmap=plt.cm.Greys_r,aspect='auto')

	plt.subplot(222)
	plt.plot(interp_projections);
	plt.ylim([inter_min,inter_max])
	plt.title("Projections at\nall degrees")
	# Add a legend for the angle colors. 
	plt.xlabel("Projection axis");
	plt.ylabel("Intensity");
	plt.subplots_adjust(hspace=0.4, wspace=0.5)

	plt.subplot(223)
	plt.title("FBP Reconstruction\nfrom sinogram")
	#plt.contourf(reconstruction)
	plt.imshow(reconstruction, cmap=plt.cm.Greys_r)
	# give it a regular sized legend. 
	plt.clim(minimal_value_fbp, maximal_value_fbp)
	plt.colorbar()

	plt.subplot(224)
	plt.title("SART Reconstruction\nfrom sinogram")
	# plt.imshow(reconstruction_sart2, cmap=plt.cm.Greys_r)
	plt.imshow(rad, cmap=plt.cm.Greys_r)
	plt.clim(minimal_value_sart, maximal_value_sart)
	plt.colorbar()

	canvas.draw()       # draw the canvas, cache the renderer
	figimage = np.fromstring(canvas.tostring_rgb(), dtype='uint8')
	figimage = figimage.reshape(fig.canvas.get_width_height()[::-1] + (3,))
	imagearray.append(figimage)
	# plt.show()
# scipy.misc.imsave(str(j)+"out.png", reconstruction)
imageio.mimsave(ss+'.gif', imagearray)
# 
# put correct labels(like angles on sinogram) on all axes. 
# 
# have ui for real-time datastreaming. 
# it should have sliders to control contrast. 
# what is the application here?
# 
# change in a cross-section medium over time?
# 
# different voltage or frequency may improve resolution?
# 
# commercial systems have 32 electrodes, 50 images per second
# 