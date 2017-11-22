# 
# This one just opens a port(after looking at what ports there are available), and puts it in a file. 
# 
import serial, time
import sys
import glob
import struct 
from serial.tools import list_ports
import numpy as np

port_list 		= list_ports.comports()
ports 			= np.array(port_list)[:,0]
print ports

port = port_list[1][0]

ser = serial.Serial()

ser.port = port

ser.baudrate = 115200

ser.bytesize = serial.EIGHTBITS # number of bits per bytes. 

ser.parity = serial.PARITY_NONE

ser.stopbits = serial.STOPBITS_ONE  # no of stopbits. 

ser.timeout = None      #block read

# ser.timeout = 1      #non-block read

# ser.timeout = 2        #timeout block read

ser.xonxoff = False     #disable software flow control

ser.rtscts = False     #disable hardware (RTS/CTS) flow control

ser.dsrdtr = False       #disable hardware (DSR/DTR) flow control

ser.writeTimeout = 2   #timeout for write

try: 
	ser.open()
	print 'yo'
except Exception, e:
	print "error open serial port: " + str(e)
	exit()
n = 0 
if ser.isOpen():

	try:
		print 'trying'
		# ser.flushInput()  #flush input buffer, discarding all its contents
		# ser.flushOutput() #flush output buffer, aborting current output 
		# 
		# and discard all that is in buffer
		# write data
		# ser.write("AT+CSQ")
		# print("write data: AT+CSQ")
		# time.sleep(0.5)  #give the serial port sometime to receive the data
		# 
		# numOfLines = 0
		# print n

		data	= ser.readline() 

		n = n+1
		while True:
			# print n 
			# f = open('data','ab')
			# print 'reading'
			response	= ser.readline() # Parse line of serial data.
			# response = ser.read() # reads one character at a time. 
			print response
			# write to file. 
			# f.write(response)
			# f.close()
		# ser.close()

	except KeyboardInterrupt: # Exception, e1:
		ser.close()
		print("Done")
		# break
		# print "error communicating...: " + str(e1)
else:
	print "cannot open serial port "


