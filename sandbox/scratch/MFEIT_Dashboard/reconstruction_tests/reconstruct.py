""" 
  First attempt at static back projection reconstruction
  for electrical impedance tomography project. 

"""
import string
import numpy as np
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import matplotlib.animation as animation


sinogram_ids = np.array([ [0,0,46,0,37,0,28,0,0], 
		[0,56,0,47,0,38,0,12,0],
		[0,0,57,0,48,0,13,0,0],
		[0,67,0,58,0,14,0,13,0],
		[0,0,68,0,15,0,24,0,0],
		[0,78,0,16,0,25,0,34,0],
		[0,0,17,0,26,0,35,0,0],
		[0,18,0,27,0,36,0,45,0],
		[0,0,28,0,37,0,46,0,0]
		])
# sinogram_ids = np.array([ [0,46,37,28,0,0], 
# 		[0,56,47,38,12,0],
# 		[0,57,48,13,0,0],
# 		[0,67,58,14,13,0],
# 		[0,68,15,24,0,0],
# 		[0,78,16,25,34,0],
# 		[0,17,26,35,0,0],
# 		[0,18,27,36,45,0],
# 		[0,28,37,46,0,0]
# 		])
logfile = [12,13,14,15,16,17,18,23,24,25,26,27,28
,34,35,36,37,38,45,46,47,48,56,57,58,67,68,78]

x,y = sinogram_ids.shape
print x,y
sinogram_ids = sinogram_ids.flatten()	

theta = [0,22.5,45,67.5,90,112.5,135,167.5,180] # 9 values. 


"""
FILE PARSING
"""
#fname = "datasets/big_glass.log"
fname = "datasets/shotglassinmiddle.log"
#fname = "datasets/shotglasshorizontalandrotated.log"
# fname = "datasets/shotglassanticlockwise.log"
#fname = "datasets/BigGlassAntiClockwise.log"

n=0
lines = []
with open(fname, "r") as f:
	for line in f:
		if "magnitudes" in line:
			lines.append(line)

			print n
			# remove the letters, commas and convert to floats. 
			datastring = lines[n].rstrip().replace(" ","").split(':')[1].split(',')
			#print datastring
			data = map(float, datastring[:-1]) # remove the trailing element after the comma. 
			sinogram_flat = np.zeros(len(sinogram_ids))
			# for j in sinogram_ids:
			for i in logfile:
				for j in range(0, len(sinogram_ids)-1):
					if i == sinogram_ids[j]:
						# i need the index of this occurance in the logfile. 
						ind = logfile.index(i)
						sinogram_flat[j]=data[ind]
			# print sinogram_flat

			sinogram = sinogram_flat.reshape([x,y]).transpose()
			# 
			# angle, pixels. 
			# plt.imshow(sinogram, interpolation='nearest')
			# plt.show()
			from skimage.transform import iradon

			reconstruction_fbp = iradon(sinogram, theta=theta, circle=True)
			# #error = reconstruction_fbp - image
			# #print('FBP rms reconstruction error: %.3g' % np.sqrt(np.mean(error**2)))

			imkwargs = dict(vmin=-0.2, vmax=0.2)
			fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4.5), sharex=True, sharey=True, subplot_kw={'adjustable':'box-forced'})
			ax1.set_title("Reconstruction\nFiltered back projection")
			ax1.imshow(reconstruction_fbp, cmap=plt.cm.Greys_r)
			ax2.set_title("Radon Transform")
			ax2.imshow(sinogram, cmap=plt.cm.Greys_r, **imkwargs)
			# plt.show()

			# from skimage.transform import iradon_sart

			# reconstruction_sart = iradon_sart(sinogram, theta=np.array(theta))
			#error = reconstruction_sart - image
			#print('SART (1 iteration) rms reconstruction error: %.3g'
			#      % np.sqrt(np.mean(error**2)))

			# fig, ax = plt.subplots(1, 2, figsize=(8, 8.5), sharex=True, sharey=True, subplot_kw={'adjustable':'box-forced'})
			# ax1, ax2 = ax.ravel()
			# ax1.set_title("Reconstruction\nSART")
			# ax1.imshow(reconstruction_sart, cmap=plt.cm.Greys_r)
			# # Run a second iteration of SART by supplying the reconstruction
			# # from the first iteration as an initial estimate
			# reconstruction_sart2 = iradon_sart(sinogram, theta=np.array(theta),
			#                                    image=reconstruction_sart)
			# ax2.set_title("SART2")
			# ax2.imshow(reconstruction_sart2, cmap=plt.cm.Greys_r)


			#error = reconstruction_sart2 - image
			#print('SART (2 iterations) rms reconstruction error: %.3g'
			#      % np.sqrt(np.mean(error**2)))

			# ax3.set_title("Reconstruction\nSART, 2 iterations")
			# ax3.imshow(reconstruction_sart2, cmap=plt.cm.Greys_r)
			# ax4.set_title("Reconstruction error\nSART, 2 iterations")
			#ax4.imshow(reconstruction_sart2 - image, cmap=plt.cm.Greys_r, **imkwargs)
			#plt.show()
			plt.savefig(str(n)+'foo.png', bbox_inches='tight')
			n=n+1