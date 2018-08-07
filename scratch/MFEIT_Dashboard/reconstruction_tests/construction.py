"""

1. Simulate the image, determine the ideal sinogram for it. - Done. 
2. Then re-create the image from the data, and create a sinogram from it. 
3. Compare 1 and 2. Error lies here. 

"""
import matplotlib.pyplot as plt
import scipy.misc
import numpy as np
#from skimage.draw import line_aa
#from skimage.draw import circle_perimeter_aa
from skimage.draw import (line_aa, circle,
                          circle_perimeter_aa)
from skimage.draw import line, set_color
from skimage.viewer import ImageViewer
from matplotlib import cm
fname = "datasets/big_glass.log"
#fname = "datasets/shotglass2.log"
# fname = "datasets/shotglassinmiddle.log"
#fname = "datasets/shotglasshorizontalandrotated.log"
# fname = "datasets/shotglassanticlockwise.log"
#fname = "datasets/BigGlassAntiClockwise.log"

n 		= 0
lines 	= []
with open(fname, "r") as f:
	for line in f:
		if "magnitudes" in line:

			if len(line) == 438:
				#	print 'here'
				# remove the letters, commas and convert to floats. 
				datastring = line.rstrip().replace(" ","").split(':')[1].split(',')
				#print datastring
				data = map(float, datastring[:-1]) # remove the trailing element after the comma. 
				lines.append(data)
				n=n+1	
	
print len(lines)	
logfile = [12,13,14,15,16,17,18,23,24,25,26,27,28
,34,35,36,37,38,45,46,47,48,56,57,58,67,68,78]			
"""
2. 
"""
image_pixels = 10
# draw a circle outline for now.
img = np.zeros((image_pixels, image_pixels), dtype=np.float)
# then find all the 8 points where electrodes are. 
x_center = image_pixels/2
y_center = image_pixels/2
radius 	 = image_pixels/2 - image_pixels/10
# this is our series of coordinates to create lines from. 
r,c,val = circle_perimeter_aa(x_center, y_center, radius)
#img[r, c] = val * 255

# electrode points: 
theta_points=[np.pi,5*np.pi/4,3*np.pi/2,7*np.pi/4,0,np.pi/4,np.pi/2,3*np.pi/4]
n1 = np.add(x_center*np.ones(len(theta_points)) , radius*np.cos(theta_points)) #  shift center
n2 = np.add(y_center*np.ones(len(theta_points)) , radius*np.sin(theta_points)) #
x = []
y = []
for i in xrange(len(n1)):
	x.append(int(n1[i]))
	y.append(int(n2[i]))
j = 0
#img[x[j], y[j]] = 255 # electrodes
# 
# the middle is 50
print x,y
# set_color(img, (n1, n2), 50)
# set_color(img, (rr, cc), 1)
# lines 


for j in xrange(len(lines)):
	data = lines[j]
	# 8 choose 2
	for i in xrange(28):
		number = str(logfile[i])
		point1,point2 = int(number[0])-1, int(number[1])-1
		# print point1,point2
		# get the line coords by parsing logfile identity order string
		l_x, l_y, val = line_aa(x[point1], y[point1], x[point2], y[point2])
		img[l_x, l_y] = img[l_x, l_y]+int(data[i])
		print data[i]

# how to put a scale on image? 
print img 
fig, ax = plt.subplots()
# imgplot = plt.imshow(img)
cax = ax.imshow(img, interpolation='nearest', cmap=cm.coolwarm)
ax.set_title('Its a drinking glass')
print img.min(),img.max()
# Add colorbar, make sure to specify tick locations to match desired ticklabels
cbar = fig.colorbar(cax, ticks=[img.min(), 0, img.max()])
# cbar.ax.set_yticklabels(['< -1', '0', '> 1'])  # vertically oriented colorbar
# cax = ax.imshow(data, interpolation='nearest', cmap=cm.afmhot)
plt.show()
# viewer = ImageViewer(img)
# viewer.show()

# x_coords,y_coords = get_line_coords(image_pixels)
# img = np.zeros((image_pixels, image_pixels), dtype=np.uint8)
# rr, cc, val = line_aa(1, 1, 80, 80)
# img[rr, cc] = val * 255
# scipy.misc.imsave("out.png", img)


