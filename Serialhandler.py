# Serial handler class. 
import serial
import sys
import time
import multiprocessing as mp
import os 
from array import array 

class Serialhandler(mp.Process):

	def __init__(self):
		mp.Process.__init__(self)
		# shared data. 
		self.connectGui 	= mp.Value('d',False)
		self.isRecording 	= mp.Value('d',False)

		# internal byte buffers. 
		self.curBytes 		= b'' # array('c','') 
		self.bytes 			= b'' # array('c','')
		self.b 				= b'' # array('c','')
		self.ser 			= []
		self.fid 			= 0 

	def sendline(self):
		# 
		# now self.bytes contains a bunch of stuff. 
		# something is up with this line. 
		indices = [i for i, s in enumerate(self.bytes) if ord(':') == s]

		line = b''
		remnant_bytes = b''
		# get a single line. 
		if len(indices) >= 1:
			if len(indices) == 1:
				# we only want one line. 
				line = self.bytes[indices[0]+1:-1]
				datastring  = line.replace(b" ",b"").split(b',')
				if len(datastring) == 29: 
					self.single_line = datastring[0:-1]
					# Now, clear that line off the bytelist. 
					self.bytes = b''
			else: 
				line = self.bytes[indices[0]+1:indices[1]-1]
				datastring  = line.replace(b" ",b"").split(b',')
				if len(datastring) == 29: 
					remnant_bytes = self.bytes[indices[1]-1:]

					self.single_line = datastring[0:-1]
					# Now, clear that line off the bytelist. 
					self.bytes = remnant_bytes
					# print 'multiline: remnant bytes', len(remnant_bytes)
		# print 'bytebuffer: ',len(self.bytes)
		# if len(self.bytes) < 400: 
		# 	print ('incomplete line:',self.bytes)

		return self.single_line

	def getserialdata(self):
		# 
		# This can be running asynchronously to the data parsing. 
		# 
		if self.ser != [] and self.connectGui == True:
			if self.ser.inWaiting() > 0:
				self.curBytes = self.ser.read(self.ser.inWaiting())
				self.bytes    = self.bytes + self.curBytes

				if self.isRecording is True: # it never gets in here? 
					# print 'recording: self.b',len(self.b),len(self.recorded_bytes)
					self.b = self.b + self.curBytes
					self.recorded_bytes = self.b
		
	def get_len_bytes(self):
		# self.bytes = ''
		return len(self.bytes)
		
	def connect(self, port_selection):

		print ('[%s] running ...  process id: %s\n' % (self.name, os.getpid()))

		if self.connectGui == True:
			self.connectGui = False
			try:
				self.ser.close()
				print ("disconnected '" + port_selection + "'")
			except:
				print ("couldnt disconnect '" + port_selection + "'")
				pass
			self.ser   = []
			# self.bytes = ''
		else:
			# print "got port '" + port_selection + "'"
			if False:
				print ('something is up')
				# check for serial port here
				pass
			else:
				try:
					self.ser 		 	= serial.Serial()
					self.ser.port 	 	= port_selection
					self.ser.baudrate 	= 115200
					self.ser.bytesize 	= serial.EIGHTBITS 	# number of bits per bytes. 
					self.ser.parity 	= serial.PARITY_NONE
					self.ser.stopbits 	= serial.STOPBITS_ONE  # no of stopbits. 
					self.ser.timeout  	= None      	 # block read
					# self.ser.timeout 	= 1      	 	 # non-block read
					# self.ser.timeout 	= 2        	 # timeout block read
					self.ser.xonxoff 	 = False     # disable software flow control
					self.ser.rtscts 	 = False     # disable hardware (RTS/CTS) flow control
					self.ser.dsrdtr 	 = False     # disable hardware (DSR/DTR) flow control
					self.ser.writeTimeout = 2   	 	 # timeout for write
					self.ser.open()
					self.connectGui = True
					print ('Now connected to ' + self.ser.port)
					sys.stdout.flush()

				except:
					print ('Cannot connect to ' +  port_selection)
					self.connectGui = False
					sys.stdout.flush()

	def record_toggle(self):

		if self.isRecording == True: # It's already recording, so close it. 
			print ('stop it recording: ', len(self.b),len(self.recorded_bytes))
			timestr = time.strftime("%Y%m%d-%H%M%S")
			self.fid = open('data_' + timestr + '.bin', 'ab')
			self.fid.write(self.b)
			self.fid.close()
			self.isRecording = False
		else:
			print ('start recording')
			self.isRecording = True

	def getbytesize(self):
		self.bytes = self.bytes + 2 
		return self.bytes



