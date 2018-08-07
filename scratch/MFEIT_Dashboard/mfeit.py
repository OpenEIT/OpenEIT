import json
from pylab import *
from scipy.stats.stats import pearsonr
import pickle
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
from scipy.stats import linregress
# 
# Open 4 spectrums
# sweet potato
# water cup
# baseline area of water cup
# baseline area of sweet potato
# 
# Day 2 of each of the above things to see if it works the next day on previous day trained signatures. 
# Average over more signatures to create the base signature. 
# 
# 
# Put all graphs on single plot with a legend. 
with open("datasets/apple1.txt", "r") as infile:
	a1_spectrum = json.load(infile)
with open("datasets/apple2.txt", "r") as infile:
	a2_spectrum = json.load(infile)
with open("datasets/apple3.txt", "r") as infile:
	a3_spectrum = json.load(infile)

with open("datasets/day2apple1.txt", "r") as infile:
	a4_spectrum = json.load(infile)
with open("datasets/day2apple2.txt", "r") as infile:
	a5_spectrum = json.load(infile)
with open("datasets/day2apple3.txt", "r") as infile:
	a6_spectrum = json.load(infile)
with open("datasets/day2apple4.txt", "r") as infile:
	a7_spectrum = json.load(infile)

with open("datasets/emptywater1.txt", "r") as infile:
	w1_spectrum = json.load(infile)
with open("datasets/emptywater2.txt", "r") as infile:
	w2_spectrum = json.load(infile)
with open("datasets/day2water1.txt", "r") as infile:
	w3_spectrum = json.load(infile)
with open("datasets/day2water2.txt", "r") as infile:
	w4_spectrum = json.load(infile)



with open("datasets/sweetpotato1.txt", "r") as infile:
	sp1_spectrum = json.load(infile)
with open("datasets/sweetpotato2.txt", "r") as infile:
	sp2_spectrum = json.load(infile)
with open("datasets/sweetpotato3.txt", "r") as infile:
	sp3_spectrum = json.load(infile)
with open("datasets/day2sweetpotato1.txt", "r") as infile:
	sp4_spectrum = json.load(infile)
with open("datasets/day2sweetpotato2.txt", "r") as infile:
	sp5_spectrum = json.load(infile)
with open("datasets/day2sweetpotato3.txt", "r") as infile:
	sp6_spectrum = json.load(infile)
with open("datasets/day2sweetpotato3.txt", "r") as infile:
	sp7_spectrum = json.load(infile)


sf  = [200,500,800, 1000,2000,5000,8000,10000,15000,20000,30000,40000,50000,60000,70000]
# fig = plt.figure(figsize=(5, 4))
# ax  = fig.add_subplot(111)
# plt.plot(sf,a1_spectrum,marker="o",linestyle='--',color='green',label='apple1')
# plt.plot(sf,a2_spectrum,marker="o",linestyle='--',color='green',label='apple2')
# plt.plot(sf,a3_spectrum,marker="o",linestyle='--',color='green',label='apple3')
# plt.plot(sf,a4_spectrum,marker="o",linestyle='--',color='green',label='appled2')
# plt.plot(sf,a5_spectrum,marker="o",linestyle='--',color='green',label='appled2')
# plt.plot(sf,a6_spectrum,marker="o",linestyle='--',color='green',label='appled2')
# plt.plot(sf,a7_spectrum,marker="o",linestyle='--',color='green',label='appled2')


# plt.plot(sf,w1_spectrum,marker="o",linestyle='--',color='blue',label='water1')
# plt.plot(sf,w2_spectrum,marker="o",linestyle='--',color='blue',label='water2')
# plt.plot(sf,w3_spectrum,marker="o",linestyle='--',color='blue',label='water1d2')
# plt.plot(sf,w4_spectrum,marker="o",linestyle='--',color='blue',label='water2d2')


# plt.plot(sf,sp1_spectrum,marker="o",linestyle='--',color='red',label='sweet_potato1')
# plt.plot(sf,sp2_spectrum,marker="o",linestyle='--',color='red',label='sweet_potato2')
# plt.plot(sf,sp3_spectrum,marker="o",linestyle='--',color='red',label='sweet_potato3')
# plt.plot(sf,sp4_spectrum,marker="o",linestyle='--',color='red',label='sweet_potatod2')
# plt.plot(sf,sp5_spectrum,marker="o",linestyle='--',color='red',label='sweet_potatod2')
# plt.plot(sf,sp6_spectrum,marker="o",linestyle='--',color='red',label='sweet_potatod2')
# plt.plot(sf,sp7_spectrum,marker="o",linestyle='--',color='red',label='sweet_potatod2')

# # 
# plt.grid(True)
# plt.xlabel('Excitation Frequencies(Hz)')
# plt.ylabel('Amplitudes')
# plt.title('Fruit spectrums in a water bath')
# plt.legend()
# plt.show()

outfile = 'datasets/day2water1.pkl'
# load data from pkl file
with open(outfile, "rb") as fp:
    d = pickle.load(fp)
#     
# print (d[500][50][50])
# fig, ax = plt.subplots()
# im = ax.imshow(d[1000], cmap=plt.get_cmap('hot'), interpolation='nearest')
# fig.colorbar(im)
# plt.show()

spectrum_array = []  
freqs = []
for key in sorted(d):
	freqs.append(key)
	spectrum_array.append(d[key])
specs = np.asarray(spectrum_array)
# print(freqs)
no_freqs,no_xpix,no_ypix = specs.shape

corr_map_apple = np.zeros([100,100])
corr_map_water = np.zeros([100,100])
corr_map_sweetpotato = np.zeros([100,100])
# Now iterate through every pixel 

# specrange 

specrange_min = 0
specrange_max = 15

for i in range(no_xpix):
	for j in range(no_ypix):
		spec = specs[:,i,j]
		slope,intercept,r,p,stderr = linregress(spec[specrange_min:specrange_max], a1_spectrum[specrange_min:specrange_max])
		corr_map_apple[i,j] = r**2
		slope,intercept,r,p,stderr = linregress(spec[specrange_min:specrange_max], w1_spectrum[specrange_min:specrange_max])
		corr_map_water[i,j] = r**2		
		slope,intercept,r,p,stderr = linregress(spec[specrange_min:specrange_max], sp1_spectrum[specrange_min:specrange_max])
		corr_map_sweetpotato[i,j] = r**2

### 
image1 = specs[1,:,:]
# image2 = specs[14,:,:]

# 5th frequency along is where sweet potato is lower. 
# consistently lower for 5 and 6. 
image2 = specs[5,:,:]

# Plot the original image(or one of them)
# Plot the correlation with itself
# Plot the correlation with each of the other items
# i.e. correlate the image with other spectra


fig = plt.figure()
ax1 = plt.subplot(221)
im1 = ax1.imshow(image1, cmap=plt.get_cmap('hot'), interpolation='nearest')
fig.colorbar(im1)
ax1.set_title('raw image@200Hz')
ax2 = plt.subplot(222)
im2 = ax2.imshow(corr_map_water, cmap=plt.get_cmap('hot'), interpolation='nearest')
fig.colorbar(im2)
ax2.set_title('correlated with water')
ax3 = plt.subplot(223)
im3 = ax3.imshow(corr_map_apple, cmap=plt.get_cmap('hot'), interpolation='nearest')
fig.colorbar(im3)
ax3.set_title('correlated with apple')
ax4 = plt.subplot(224)
im4 = ax4.imshow(corr_map_sweetpotato, cmap=plt.get_cmap('hot'), interpolation='nearest')
fig.colorbar(im4)
ax4.set_title('correlated with sweetpotato')
plt.show()
# 
# 
# The question is now, how to combine them. 
# dumb 3 class classifier, uses threshold to select between 3 values. 
# 
# 
# Final image. 
# 3 sliders, one for each water/apple/sweetpotato
# 
# apple is green
# sweet potato is red
# water is shade of blue? 
# 
from matplotlib.widgets import Slider, Button, RadioButtons

def modify(water,apple,sweetpotato,corr_map_sweetpotato,corr_map_apple,corr_map_water):

	it = 0 
	amplitude = 0.0
	amplitude2 = 0.0
	class_map = np.zeros([100,100])
	I  = np.dstack([class_map, class_map, class_map])
	for i in range(no_xpix):
		for j in range(no_ypix):
			if corr_map_water[i,j] > water: 
				# I[i, j, :] = [0, 0, corr_map_water[i,j]]		
				amplitude = amplitude + specs[1,i,j]
				amplitude2 = amplitude2 + specs[5,i,j]
				it = it+1 

	mean_amp  = amplitude/it
	mean_amp2 = amplitude2/it

	for i in range(no_xpix):
		for j in range(no_ypix):

			if corr_map_apple[i,j] > apple and specs[1,i,j] > mean_amp: # less conductive, higher amplitude
				I[i, j, :] = [0, 1, 0]

			if corr_map_sweetpotato[i,j] > sweetpotato: # and specs[5,i,j] < mean_amp2: # more conductive, lower amplitude
				I[i, j, :] = [1, 0, 0]

			if corr_map_water[i,j] > water: 
				I[i, j, :] = [0, 0, 1]

	out_image = I 
	return out_image
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig, ax = plt.subplots()
plt.subplots_adjust(left=0.15, bottom=0.35)
class_map = np.zeros([100,100])

class_map = modify(0.5,0.5,0.5,corr_map_sweetpotato,corr_map_apple,corr_map_water)
im = ax.imshow(class_map , interpolation='nearest')

# fig.colorbar(im)
ax.set_title('Class Map')


colors = [(1.0,0.0,0.0,1.0),(0.0,1.0,0.0,1.0),(0.0,0.0,1.0,1.0)]
labels = ['sweet potato','apple','water']
print (colors)
# create a patch (proxy artist) for every color 
patches = [ mpatches.Patch(color=colors[i], label=labels[i])  for i in range(len(labels)) ]
# patches = [ mpatches.Patch(color=[(0.0,1.0,0.0,1.0),(0.0,1.0,0.0,1.0),(0.0,1.0,0.0,1.0)], label=['red','green','blue']) ]
# put those patched as legend-handles into the legend
plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0. )


# ax.legend(['apple','sweetpotato','water'])
axcolor = 'lightgoldenrodyellow'
axwater = plt.axes([0.15, 0.1, 0.65, 0.03], facecolor=axcolor)
axapple = plt.axes([0.15, 0.15, 0.65, 0.03], facecolor=axcolor)
axsweetpotato = plt.axes([0.15, 0.2, 0.65, 0.03], facecolor=axcolor)

sw = Slider(axwater, 'Water', 0.0, 1.0, valinit=0.5)
sa = Slider(axapple, 'Apple', 0.0, 1.0, valinit=0.5)
ssp = Slider(axsweetpotato, 'SweetPotato', 0.0, 1.0, valinit=0.5)

def update(val):
    water 		= sw.val
    apple 		= sa.val
    sweetpotato = ssp.val
    class_map = modify(water,apple,sweetpotato,corr_map_sweetpotato,corr_map_apple,corr_map_water)
    # This is where we modify corr_map
    im.set_array(class_map)
    fig.canvas.draw_idle()

sw.on_changed(update)
sa.on_changed(update)
ssp.on_changed(update)
plt.show()



# Take 4 new files. Save the dictinary(freq *img) and also take a photo of the item in the phantom. 
# 
# 1. nothing. 
# 2. water cup
# 3. sweet potato
# 4. sweet potato on one side, water cup on the other. 
# 
# 
# Do pearson cross-correlation with every 'pixel' in the image. 
# and plot the result of this on a new image. 
# 3 images to show match against 3 signatures: 
# 
# Ideally subject of interest will be easier to see than other 3, and can manually set thresholds. 
# 
# Regenerate a combined (3 signature) tested image, with thresholds appropriately set, for all recorded datasets. 
# 
# 


