# 
# This one just opens a port(after looking at what ports there are available), and puts it in a file. 
# 
import serial, time
import sys
import glob
import struct 

def serial_ports():
	""" Lists serial port names

		:raises EnvironmentError:
			On unsupported or unknown platforms
		:returns:
			A list of the serial ports available on the system
	"""
	if sys.platform.startswith('win'):
		ports = ['COM%s' % (i + 1) for i in range(256)]
	else:
		raise EnvironmentError('Unsupported platform')

	result = []
	for port in ports:
		try:
			s = serial.Serial(port)
			s.close()
			result.append(port)
		except (OSError, serial.SerialException):
			pass
	return result

print(serial_ports())


ser = serial.Serial()

ser.port = 'COM3'

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
		numOfLines = 0

		while True:
			f = open('data','ab')
			# print 'reading'
			response = ser.read()
			print response
			# write to file. 
			f.write(response)
			f.close()
		ser.close()

	except Exception, e1:
		print "error communicating...: " + str(e1)
else:
	print "cannot open serial port "


