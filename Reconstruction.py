"""

Helper functions

"""
import multiprocessing as mp
import ctypes

import matplotlib
import scipy.misc
import numpy as np
import imageio
from skimage.draw import line as ll
from skimage.draw import (line_aa, circle,
                          circle_perimeter_aa)
from skimage.draw import line, set_color
from skimage.viewer import ImageViewer
from matplotlib import cm
from skimage import data_dir
from skimage.transform import radon, iradon
from scipy.ndimage import zoom
from skimage.transform import iradon_sart

# def readlog(fname):

# 	ss = fname.split("/")[1][0:-4]
# 	imagearray = []
# 	n 		= 0
# 	lines 	= []
# 	with open(fname, "r") as f:
# 		for l in f:
# 			if "magnitudes" in l:
# 				if len(l) >= 200: #438:
# 					#	print 'here'
# 					# remove the letters, commas and convert to floats. 
# 					datastring = l.rstrip().replace(" ","").split(':')[1].split(',')
# 					#print datastring
# 					data = map(float, datastring[:-1]) # remove the trailing element after the comma. 
# 					lines.append(data)
# 					n=n+1	
# 	return lines

"""
	Reconstruction Algorithm 

"""
class Reconstruction(mp.Process):

	def __init__(self):
		mp.Process.__init__(self)
		# print '[%s] running ...  process id: %s\n' % (self.name, os.getpid())

		self.image_pixels 			= 100 # problem, if I go down to say, 10, then some of the lines aren't displayed. 
		self.minimal_value_fbp 		= 0
		self.maximal_value_fbp 		= 40000
		self.minimal_value_sart 	= 0
		self.maximal_value_sart 	= 40000
		self.inter_min				= 0
		self.inter_max				= 100000

		self.img					= np.zeros((self.image_pixels, self.image_pixels), dtype=np.float)
		self.baseline_image 		= np.zeros((self.image_pixels, self.image_pixels), dtype=np.float)
		# 
		# Above should be calculated elsewhere and is only for plotting purposes. 
		# 
		self.x_center 			= self.image_pixels/2
		self.y_center 			= self.image_pixels/2
		self.radius 	 		= self.image_pixels/2 - self.image_pixels/10
		# 
		# Log file order, 8 choose 2. 
		self.logfile = [12,13,14,15,16,17,18,23,24,25,26,27,28,34,35,36,37,38,45,46,47,48,56,57,58,67,68,78]	
		# electrode points: 
		self.theta_points=[np.pi,5*np.pi/4,3*np.pi/2,7*np.pi/4,0,np.pi/4,np.pi/2,3*np.pi/4]
		# 180,225,270,315,0,45,90,135
		# 1,2,3,4,5,6,7,8

		## multiprocessing image to share. 
		self.shared_image = mp.Array(ctypes.c_float,100*100)

	def makeimages(self,data):

		# what is this n thing?
		n1 = np.add(self.x_center*np.ones(len(self.theta_points)) , self.radius*np.cos(self.theta_points)) #  shift center
		n2 = np.add(self.y_center*np.ones(len(self.theta_points)) , self.radius*np.sin(self.theta_points)) #
		# 
		x = []
		y = []
		for i in xrange(len(n1)):
			x.append(int(n1[i]))
			y.append(int(n2[i]))

		firstreconstruction = []

		d 		= dict()
		# 8 choose 2
		for i in xrange(28):
			number = str(self.logfile[i])
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
			img = np.zeros((self.image_pixels, self.image_pixels), dtype=np.float)
			for a in d: 
				if abs(a-(angle))<5:
					# print a, angle
					img 			= d[a]
					img[l_x, l_y] 	= img[l_x, l_y]+data[i]
					# build up the image for each angle. 
					d[a]=img
					mark = 1
			if mark == 0: # if it doesn't already exist. 
				img[l_x, l_y] = data[i]
				# create a new array in this slot
				d[angle] = img

			deg = []
			for key in d:
				deg.append(key)
			keyz = deg
			# 

		return d, deg

	def reconstruct(self,d,deg):

		interp_projections = []
		# Now interpolate for each angled projection, and place back into the projection. 
		for i in xrange(len(deg)):
			# print 'degrees: ',deg[i],d[deg[i]].shape, deg
			# sinogram = radon(image, theta=theta, circle=True)
			projections = radon(d[deg[i]], theta=deg, circle= True)
			# print 'projections shape',projections.shape
			p = projections[:,i]
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
			# print xp, yp
			# Now interpolate to acquire 
			xnew = np.linspace(0, len(p),len(p))
			# print len(xnew)
			yinterp = np.interp(xnew, xp, yp)
			interp_projections.append(yinterp)

		interp_projections = np.array(interp_projections).transpose()

		# reconstruction = iradon(interp_projections, theta=deg, circle=True)
		# SART reconstruction: 
		reconstruction_sart = iradon_sart(interp_projections, theta=np.array(deg))
		reconstruction_sart2 = iradon_sart(interp_projections, theta=np.array(deg),
	                                   image=reconstruction_sart)

		image 	 = reconstruction_sart2
		self.img = image 
		return image

	def eit_reconstruction(self,data): 
		
		d, deg = self.makeimages(data)
		
		image = self.reconstruct(d,deg)
		
		# self.img - self.baseline_image
		# self.image_reconstruct.subtract_baseline()		
		# self.shared_image = self.img - self.baseline_image			
		return image - self.baseline_image

	def set_baseline(self): 
		self.baseline_image = self.img

	def subtract_baseline(self): 
		# remove the baseline. 
		return self.img - self.baseline_image
