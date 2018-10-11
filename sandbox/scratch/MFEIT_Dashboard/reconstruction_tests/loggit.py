import serial
import time
from pylab import *
import datetime
import numpy
import matplotlib.pyplot as plt
import matplotlib.animation as animation

fig 	= plt.figure()
p1 		= fig.add_subplot(211)
p2 		= fig.add_subplot(212)
# fig, (ax1,ax2) = plt.subplots(2,1,sharex=True)
class StdOutListener():
  def __init__(self):
    self.start_time 	= time.time()
    self.x 				= []
    self.y 				= []
    self.my_average 	= []
    self.line_actual,   = p1.plot(self.x, self.y)                  # line stores a Line2D we can update
    self.line_average, 	= p1.plot(self.x, self.my_average)       # line stores a Line2D we can update
    # Second plot: 
    self.x2 			= []
    self.y2 			= []
    self.my_average2 	= []
    self.line_actual2, 	= p2.plot(self.x2, self.y2)                  # line stores a Line2D we can update
    self.line_average2, = p2.plot(self.x2, self.my_average2)       # line stores a Line2D we can update    

  def on_data(self, new_value,new_value2):
    plt.pause(0.001)
    # .subplot(211)
    time_delta = time.time() - self.start_time                # on our x axis we store time since start
    # print new_value,time_delta
    self.x.append(time_delta)
    self.y.append(new_value)
    self.my_average.append(numpy.mean(self.y))
    self.line_actual.set_data(self.x, self.y)
    self.line_average.set_data(self.x, self.my_average)

    p1.add_line(self.line_actual)
    p1.add_line(self.line_average)

    # p1.ylim([min(self.y), max(self.y)])        # update axes to fit the data
    # p1.xlim([min(self.x), max(self.x)])

    p1.set_ylim([min(self.y), max(self.y)])        # update axes to fit the data
    p1.set_xlim([min(self.x), max(self.x)])

    p1.set_xlabel('magnitude')

    # Second plot 
    self.x2.append(time_delta)
    self.y2.append(new_value2)
    self.my_average2.append(numpy.mean(self.y2))
    self.line_actual2.set_data(self.x2, self.y2)
    self.line_average2.set_data(self.x2, self.my_average2)

    p2.add_line(self.line_actual2)
    p2.add_line(self.line_average2)

    p2.set_ylim([min(self.y2), max(self.y2)])        # update axes to fit the data
    p2.set_xlim([min(self.x2), max(self.x2)])
    p2.set_xlabel('phase')

    draw()                                  # redraw the plot

ion()                                       # ion() allows matplotlib to update animations.
out_listener = StdOutListener()

# End plot preparation, open serial port and start reading data.  
ser = serial.Serial('COM3', 115200)
abc = open('logFile.txt', 'a')
while True:
	try: 
		line2 		= ser.readline()
		ss 			= line2.split()
		magnitude 	= ss[3].strip(',')
		phase	 	= ss[4].strip(')')
		timeStamp   = datetime.datetime.now()
		# print(str(timeStamp),magnitude,phase)
		dataIn = str(timeStamp)+','+magnitude+','+phase
		print(dataIn)
		abc.write(dataIn+'\n')
		out_listener.on_data(float(magnitude),float(phase))
	except KeyboardInterrupt:
		print('Closing File... ')
		abc.close() 
		ser.close()
		print("Done")
		break
