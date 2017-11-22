"""
  UI for doing realtime EIT reconstruction. 

"""
# from pylab import *
from numpy import pi, sin
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.widgets import Slider, Button, RadioButtons,TextBox
from serial.tools import list_ports
from matplotlib.pyplot import figtext
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial 
import helper as h
from skimage.util import img_as_ubyte

import imageio
global readfromlogon
global readfromserial

min_cbar 		= 0
max_cbar 		= 40000

zeropoint 		= 0 
img_range 		= 40000
imagearray	    = []
ser 		 = serial.Serial()
f = open('logfile.txt','w')

writingmovie 	= False
writinglog 		= False
readfromlogon 	= False
readfromserial  = False
axis_color 		= 'oldlace'
fig 			= plt.figure(figsize=(14, 8))
fig.canvas.set_window_title('Real-time EIT reconstruction')
ax 				= fig.add_subplot(111) # Draw the plot
fig.subplots_adjust(left=0.25, bottom=0.25)
# plt.title("Reconstruction from sinogram")
cbaxes 	 		= fig.add_axes([0.8, 0.25, 0.03, 0.7]) 
lines 			= []

# Get Port defaults. 
port_list 		= list_ports.comports() # This should be one of the first things done. 
port_list		= np.array(port_list)[:,0]
portnames 		= []
fullportnames 	= []
for item in port_list:
	if 'n/a' in item:
		print 'skip it', item
	else: 
		stuff = item.split('/') # remove the prefix. 
		portnames.append(stuff[-1])
		fullportnames.append(item)
currentport = fullportnames[0]
print currentport


def to_rgb(im):
    # we can use the same array 3 times, converting to
    # uint8 first
    # this explicitly converts to np.uint8 once and is short
    return np.dstack([im.astype(np.uint8)] * 3)


# Parse data
connection_status 			= 'Status: Not Connected'
connect_text 				= plt.figtext(0.15, 0.825,connection_status)
def updatestatus(connection_status):
	connect_text.set_text(connection_status)
updatestatus(connection_status)

log_status 					= 'Status: Not Reading Log'
log_text 					= plt.figtext(0.15, 0.725,log_status)
def updatelogstatus(log_status):
	log_text.set_text(log_status)
updatelogstatus(log_status)

wlog_status 				= 'Status: Not Writing'
writelog_text 				= plt.figtext(0.19, 0.325,wlog_status)
def updatewlogstatus(wlog_status):
	writelog_text.set_text(wlog_status)
updatewlogstatus(wlog_status)

wmovie_status 				= 'Status: Not Collecting Movie'
writemovie_text 			= plt.figtext(0.19, 0.225,wmovie_status)
def updatewmoviestatus(wmovie_status):
	writemovie_text.set_text(wmovie_status)
updatewmoviestatus(wmovie_status)

class StdOutListener(): # image animation
	def __init__(self):
		self.image_pixels 			= 100     
		self.img 					= np.zeros((self.image_pixels, self.image_pixels), dtype=np.float)
		self.cax  					= ax.imshow(self.img) 

	def on_data(self, im,min_cbar,max_cbar):
		plt.pause(0.001)

		if readfromserial or readfromlogon:
			self.cax.set_array(im)
			cbar = plt.colorbar(self.cax,cax = cbaxes)
			cbar.set_clim([min_cbar,max_cbar])
			plt.draw()                                  # redraw the plot

# Add a set of radio buttons for changing UART Port. 
color_radios_ax = fig.add_axes([0.025, 0.4, 0.25, 0.2], axisbg=axis_color)
color_radios = RadioButtons(color_radios_ax, tuple(portnames), active=0)
def color_radios_on_clicked(label):
	global currentport
	for thing in fullportnames: 
		if label in thing:
			currentport = thing
	fig.canvas.draw_idle()
color_radios.on_clicked(color_radios_on_clicked)

min_scale_slider_ax = fig.add_axes([0.25, 0.15, 0.65, 0.03], axisbg=axis_color)
max_scale_slider_ax = fig.add_axes([0.25, 0.1, 0.65, 0.03], axisbg=axis_color)
min_scale_slider 	= Slider(min_scale_slider_ax, 'Contrast Min', 0, 1, valinit=0.1)
max_scale_slider 	= Slider(max_scale_slider_ax, 'Contrast Max', 0, 1, valinit=0.9)
def sliders_on_changed(val):
	global min_cbar,max_cbar,zeropoint,img_range
	if min_scale_slider.val >= max_scale_slider.val:
		print ' min slider not allowed to be larger than max slider'
	else:
		min_cbar = zeropoint+min_scale_slider.val*img_range
		max_cbar = zeropoint+max_scale_slider.val*img_range
	fig.canvas.draw_idle()
max_scale_slider.on_changed(sliders_on_changed)
min_scale_slider.on_changed(sliders_on_changed)


# Add a button for connecting via UART. 
connect_button_ax = fig.add_axes([0.025, 0.8, 0.1, 0.06])
connect_button = Button(connect_button_ax, 'Connect', color=axis_color, hovercolor='0.975')
def connect_button_on_clicked(mouse_event):
	# 
	global readfromserial, currentport, ser
	if readfromserial == True: # read .  
		if ser.isOpen(): # Means it's time to disconnect. 
			ser.close()
			updatestatus("Status: Not connected")
			connect_button.label.set_text("Connect") # works
			readfromserial = False

	elif readfromserial == False: # stop reading  
		# UART connection. 
		ser 		 = serial.Serial()
		print currentport
		ser.port 	 = currentport
		ser.baudrate = 115200
		ser.bytesize = serial.EIGHTBITS 	# number of bits per bytes. 
		ser.parity 	 = serial.PARITY_NONE
		ser.stopbits = serial.STOPBITS_ONE  # no of stopbits. 
		ser.timeout  = None      # block read
		# ser.timeout = 1      	 # non-block read
		# ser.timeout = 2        # timeout block read
		ser.xonxoff 	 = False     # disable software flow control
		ser.rtscts 		 = False     # disable hardware (RTS/CTS) flow control
		ser.dsrdtr 		 = False     # disable hardware (DSR/DTR) flow control
		ser.writeTimeout = 2   	 # timeout for write

		try: 
			ser.open()
			ser.flushInput()
			ser.flushOutput()			
			max_scale_slider.reset()
			min_scale_slider.reset()
			print 'serial line open'
			updatestatus("Status: Connected")
			connect_button.label.set_text("Disconnect") # works
			readfromserial = True
		except Exception, e:
			print "error open serial port: " + str(e)
			updatestatus("Status: Not Connected")
			readfromserial = False
connect_button.on_clicked(connect_button_on_clicked)



# Add a button for reading in a log file.  
log_button_ax 		= fig.add_axes([0.025, 0.7, 0.1, 0.06])
log_button 			= Button(log_button_ax, 'Read Log', color=axis_color, hovercolor='0.975')
def log_button_on_clicked(mouse_event):

	global readfromlogon, min_scale_slider,max_scale_slider
	if readfromlogon == True: # read from log now.  
		print 'stop reading from log'
		log_button.label.set_text("Read Log") # works
		updatelogstatus("Status: Not Reading Log")
		readfromlogon = False

	elif readfromlogon == False: # stop reading from log. 
		print 'start reading from log'
		# Read from file
		fname = "../datasets/BigGlassAntiClockwise.log"
		global lines
		lines = h.readlog(fname)
		if len(lines) > 0:
			print 'opened log successfully'
			log_button.label.set_text("Stop Read Log") # works
			updatelogstatus("Status: Reading Log")
			max_scale_slider.reset()
			min_scale_slider.reset()
			readfromlogon = True
	# print 'readfromlogon is currently: ', readfromlogon
log_button.on_clicked(log_button_on_clicked)

# Add a button for writing a log file.  
write_log_button_ax = fig.add_axes([0.025, 0.3, 0.15, 0.06])
write_log_button = Button(write_log_button_ax, 'Write Log', color=axis_color, hovercolor='0.975')
def write_log_button_on_clicked(mouse_event):
	# Read from file
	print 'writing serial data to file'
	global writinglog,f
	# if UART is open, write each line to a file. 
	# Stop writing on click or if data disconnects. 
	if writinglog == True: # stop writing log
		print 'stop writing log'
		write_log_button.label.set_text("Write Log") # works
		updatewlogstatus("Status: Not Writing")
		writinglog = False
		f.close()
		# perform the closing of the file. 

	elif writinglog == False: # start writing log. 
		print 'start reading from log'
		write_log_button.label.set_text("Stop Writing Log") # works
		updatewlogstatus("Status: Writing Log")
		f = open('logfile.txt','w')
		# consider writing a timestamp. 
		# Now open file to enable writing. 
		writinglog = True

write_log_button.on_clicked(write_log_button_on_clicked)
#
# Add a button for writing an animated gif.  
write_movie_button_ax = fig.add_axes([0.025, 0.2, 0.15, 0.06])
write_movie_button = Button(write_movie_button_ax, 'Write Movie', color=axis_color, hovercolor='0.975')
def write_movie_button_on_clicked(mouse_event):
	global writingmovie,imagearray
	if writingmovie == True: # stop writing movie
		print 'stop writing movie'
		write_movie_button.label.set_text("Write Movie") # works
		updatewmoviestatus("Status: Not Writing")
		writingmovie 	= False
		imageio.mimsave('movie.gif', imagearray,duration=0.2)
		imagearray 		= [] # clear it. 
	elif writingmovie == False: # start writing log. 
		print 'start reading from movie'
		write_movie_button.label.set_text("Stop Writing Movie") # works
		updatewmoviestatus("Status: Writing Movie")
		# save to gif when it button is pressed the second time. 
		writingmovie 	= True
		print 'writing movie to file'
write_movie_button.on_clicked(write_movie_button_on_clicked)



def minboxsubmit(text):
	global min_cbar
	min_cbar = float(eval(text))

def maxboxsubmit(text):
	global max_cbar
	max_cbar = float(eval(text))

mintxtbox = fig.add_axes([0.2, 0.8, 0.3, 0.1], axisbg=axis_color)
maxtxtbox = fig.add_axes([0.3, 0.6, 0.3, 0.1], axisbg=axis_color)
initial_text = 'enter'
mintext_box = TextBox(mintxtbox, 'Evaluate', initial=initial_text)
maxtext_box = TextBox(maxtxtbox, 'Evaluate', initial=initial_text)
mintext_box.on_submit(minboxsubmit)
maxboxsubmit.on_submit(maxboxsubmit)


# start running the thing! 
plt.ion()                                   # ion() allows matplotlib to update animations.
out_listener 		= StdOutListener()				# initialize. 
image_reconstruct 	= h.Reconstruction()
bgimg 			= np.zeros((100,100), dtype=np.float)
img 				= bgimg
n       			= 0
lastreadfromlogon	= False 
lastreadfromserial	= False 

while True:
	try: 
		if readfromlogon:

			if len(lines) == n and len(lines) != 0: # auto turn off at the end. 
				print 'end of file'
				print 'readfromlogon is currently: ', readfromlogon
				log_button.label.set_text("Start Read Log")
				readfromlogon 		= False
				updatelogstatus("Status: Not Reading Log")
				n 					= 0
				lastreadfromlogon 	= False
				readfromlogon	  	= False
			else:
				if lastreadfromlogon == False and len(lines)>0:
					print 'initializing', img
					if img.max() != 0:
						# scaling factor of color bar. 
						zeropoint = img.min() 
						img_range = img.max()-img.min()
						min_cbar  = zeropoint+min_scale_slider.val*img_range
						max_cbar  = zeropoint+max_scale_slider.val*img_range
						lastreadfromlogon = True
					else: 
						print 'error: the image is empty'
						print 'check line:',lines[n]
						data 				= lines[n]
						d, deg				= image_reconstruct.makeimages(data)
						img 				= image_reconstruct.reconstruct(d,deg)
				else:				
					print n,len(lines),min_cbar,max_cbar, zeropoint,img_range
					data 				= lines[n]
					d, deg				= image_reconstruct.makeimages(data)
					img 				= image_reconstruct.reconstruct(d,deg)
					lastreadfromlogon 	= True
					n 					= n+1

		elif readfromserial:
			if not ser.isOpen():
				readfromserial = False
			# Doesn't run out of lines. Is just turned on and off. 
			if lastreadfromserial == False:
				test = bgimg - img 
				if test.max() != 0 and bgimg.max() != 0: 
					img = test 
				# if img.max() != 0 and bgimg.max() != 0: # initialize scaling factor for colorbar. 
					zeropoint 			= img.min() 
					img_range 			= img.max() - img.min()
					min_cbar  			= zeropoint+min_scale_slider.val*img_range
					max_cbar  			= zeropoint+max_scale_slider.val*img_range				
					lastreadfromserial 	= True
					print 'initialized'
				else: 
					bytesToRead = ser.inWaiting()
					print 'first read',bytesToRead

					if bytesToRead > 0 and bytesToRead <= 400:
						print 'first good data'
						d			= ser.readline() # Parse line of serial data.
						datastring 	= d.rstrip().replace(" ","").split(':')[1].split(',')
						data 		= map(float, datastring[:-1])
						# replace zeros with a small number. 
						for i, delement in enumerate(data):
							if delement == 0:
								data[i] = 1.0

						d, deg		= image_reconstruct.makeimages(data)
						img 		= image_reconstruct.reconstruct(d,deg)
						if bgimg.max() == 0 and img.max() != 0: # assign the bg image. 
							bgimg = img
							print 'bgimg assigned'

					else:
						print 'flushed'
						if bytesToRead > 0:
							d			= ser.readline()
							print d
						ser.flushInput()
						ser.flushOutput()
			else:	
				bytesToRead = ser.inWaiting()
				print 'data in queue:', bytesToRead 

				if bytesToRead > 0 and bytesToRead <= 400:
					print 'good data'
					d			= ser.readline() # Parse line of serial data.
					datastring 	= d.rstrip().replace(" ","").split(':')[1].split(',')
					data 		= map(float, datastring[:-1])
					# replace zeros with a small number. 
					for i, delement in enumerate(data):
						if delement == 0:
							data[i] = 1.0
					d, deg		= image_reconstruct.makeimages(data)
					img 		= image_reconstruct.reconstruct(d,deg)
					img 		= bgimg - img
					print img.max(), img.min(), min_cbar, max_cbar 
					# min_cbar = img.min()
					# max_cbar = img.max()
				else:
					print 'flushing'
					# print data 
					ser.flushInput()
					ser.flushOutput()
		else:
		 	# print 'serial/log',readfromserial,readfromlogon
		 	print '.'
		out_listener.on_data(img,min_cbar,max_cbar)

		# The other two buttons for recording info. 
		if writingmovie: 
			cmap 		= plt.get_cmap('jet')
			img[img>max_cbar]=1.0
			img[img<min_cbar]=0.0
			new_range 	= max_cbar-min_cbar
			# first apply the normalization range. 
			# img = (img + abs(zeropoint))/new_range # img_range
			img = (img+abs(img.min()))/new_range
			# Now crop between min_cbar and max_cbar? 
			rgba_img 	= cmap(img)
			rgb_img 	= np.delete(rgba_img, 3, 2)
			convimg = img_as_ubyte(rgb_img)
			imagearray.append(convimg)
		if writinglog:
			f.write(data)
		
	except KeyboardInterrupt:
		print('Closing UI')
		print("Done")
		break

