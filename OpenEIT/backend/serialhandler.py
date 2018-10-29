# Serial handler class.
import time
import threading
import logging
import serial
import serial.threaded
import uuid
from OpenEIT.backend.bluetooth import Adafruit_BluefruitLE
from OpenEIT.backend.bluetooth.Adafruit_BluefruitLE.services import UART
import objc
from PyObjCTools import AppHelper
import os 

# Define service and characteristic UUIDs used by the UART service.
UART_SERVICE_UUID = uuid.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
TX_CHAR_UUID      = uuid.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')
RX_CHAR_UUID      = uuid.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')

logger = logging.getLogger(__name__)

def parse_bis_line(line):  # this parses a bioimpedance spectroscopy line.
    # 200,500,800,1000,2000,5000,8000,10000,15000,20000,30000,40000,50000,60000,70000  
    try:  # take only data after magnitudes. 
        _, data = line.split(":", 1)
    except ValueError:
        return None
    items = []
    for item in data.split(";"):
        item = item.strip()
        if not item:
            continue
        try:
            items.append(float(item))
        except ValueError:
            return None
    return items

def parse_timeseries(line):  # this parses time series data.  
    items = []
    for item in line.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            items.append(float(item))
        except ValueError:
            return None

    return items

def parse_line(line):  # this parses a whole line, i.e. 928 values at once. 
    try:  # take only data after magnitudes. 
        _, data = line.split(":", 1)
    except ValueError:
        return None

    items = []
    for item in data.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            items.append(float(item))
        except ValueError:
            return None
    return items

def parse_ble_line(line):   
    try:  # take only data after magnitudes. 
        _, data = line.split(":", 1)
    except ValueError:
        return None

    items = []
    for item in data.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            items.append(float(item))
        except ValueError:
            return None

    # force length. 
    if len(items) <928:
        # print (len(items))
        return None

    return items

# This will become the universal line parser which separates out the different types of data. 
# 
# 
def parse_any_line(line):  
    try:  
        _, data = line.split(":", 1)
    except ValueError:
        return None

    items = []
    for item in data.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            items.append(float(item))
        except ValueError:
            return None

    return items


class SerialHandler:

    def __init__(self, queue,mode):
        self._connection_lock = threading.Lock()
        self._reader_thread = None
        self._queue = queue
        #self._mpqueue = Queue()
        self._recording_lock = threading.Lock()
        self._recording = False
        self._record_file = None
        # self._data_type = data_type
        self._mode = mode

        self.raw_text = 'abc'
        # Get the BLE provider for the current  platform.
        self.ble = Adafruit_BluefruitLE.get_provider()
        # add these into the main scope of Serial handler instead of the BLE Class handler. 
        self.ble_line = ''
        self.get_line_lock = 0 
        self.device = ''
        self.stoprequest = threading.Event()

    def is_connected(self):
        with self._connection_lock:
            return self._reader_thread is not None

    def return_last_line(self):
        with self._connection_lock:
            return self.raw_text

    # this needs updating to have a bluetooth method separate from the reader_thread serial method. 
    def disconnect(self):
        with self._connection_lock:
            if self._reader_thread is None:
                return

            self._reader_thread.close()
            self._reader_thread = None

    def write(self, text):
        self._reader_thread.write(text.encode())

    def setmode(self, mode):
        self._mode = mode

    def getmode(self):
        return self._mode

    def connect(self, port_selection):
        with self._connection_lock:
            if self._reader_thread is not None:
                raise RuntimeError("serial already connected")

            print('connecting to: ', port_selection)

            if 'Bluetooth' in port_selection:
                #print ('Bluetooth Callback')
                # Initialize the BLE system.  MUST be called before other BLE calls!
                #self.ble.initialize()
                print ('initializing')
            else: 
                # configure the serial connection
                ser = serial.Serial()
                ser.port = port_selection
                ser.baudrate = 115200
                ser.bytesize = serial.EIGHTBITS
                ser.parity = serial.PARITY_NONE
                ser.stopbits = serial.STOPBITS_ONE
                ser.timeout = None
                ser.xonxoff = False
                ser.rtscts = False
                ser.dsrdtr = False
                ser.writeTimeout = 2

                try:
                    ser.open()
                    # on connect, write the mode from the config file. 
                    ser.write(self._mode.encode())
                    print ('writing mode to device')

                except serial.SerialException:
                    print ('could not connect')
                    logger.error('Cannot connect to %s', port_selection)
                    raise

            serialhandler = self

            class LineReader(serial.threaded.LineReader):

                TERMINATOR = b'\n'

                def connection_made(self, transport):
                    serialhandler._connected = True
                    super().connection_made(transport)
                    logger.info('connection made now')

                def handle_line(self, line):
                    # XXX: we should not record the raw stream but the
                    # parsed data
                    print (line)
                    serialhandler.raw_text = line

                    with serialhandler._recording_lock:
                        if serialhandler._recording:
                            logger.info("serialhandler._recording")
                            serialhandler._record_file.write(line + "\n")

                    res = parse_any_line(line)
                    # parse line based on different input data types. 
                    # if self._data_type == 'a': 
                    #     res = parse_timeseries(line)
                    # elif self._data_type == 'b':
                    #     res = parse_bis_line(line)
                    # else: 
                    #     res = parse_line(line)
                    # logger.info(res)

                    if res is not None:
                        serialhandler._queue.put(res)

                def connection_lost(self, exc):
                    if exc is not None:
                        logger.error('connection lost %s', str(exc))
                    else:
                        logger.info('connection lost')

                    with serialhandler._connection_lock:
                        if serialhandler._reader_thread is self:
                            serialhandler._reader_thread = None

            class bleThread(threading.Thread):

                def __init__(self, blehandle, queue):
                    super().__init__()
                    # Get the BLE provider for the current platform.
                    self._queue = queue
                    self.ble = blehandle
                    self.uart = None
                    # so we can process line reading 
                    self.ble_line = ''
                    self.get_line_lock = 0 
                    self.device = ''
                    self.stoprequest = threading.Event()

                def run(self):

                    while not self.stoprequest.isSet():

                        self.ble = Adafruit_BluefruitLE.get_provider()
                        self.ble.initialize()
           
                        # Clear any cached data because both bluez and CoreBluetooth have issues with
                        # caching data and it going stale.
                        self.ble.clear_cached_data()
                
                        adapter = self.ble.get_default_adapter()
        
                        adapter.power_on()

                        print('Using adapter: {0}'.format(adapter.name))
                        # Disconnect any currently connected UART devices.  Good for cleaning up and
                        # starting from a fresh state.
                        print('Disconnecting any connected UART devices...')
                        UART.disconnect_devices()

                        # Scan for UART devices.
                        print('Searching for UART device...')
                        try:
                            adapter.start_scan()
                            # Search for the first UART device found (will time out after 60 seconds
                            # but you can specify an optional timeout_sec parameter to change it).
                            self.device = UART.find_device()
                            if self.device is None:
                                raise RuntimeError('Failed to find UART device!')
                        finally:
                            # Make sure scanning is stopped before exiting.
                            adapter.stop_scan()

                        print('Connecting to ', self.device.name)
                        self.device.connect()  # Will time out after 60 seconds, specify timeout_sec parameter
                                          # to change the timeout.

                        # Once connected do everything else in a try/finally to make sure the device
                        # is disconnected when done.
                        try:
                            # Wait for service discovery to complete for the UART service.  Will
                            # time out after 60 seconds (specify timeout_sec parameter to override).
                            print('Discovering services...')
                            UART.discover(self.device)

                            # Once service discovery is complete create an instance of the service
                            # and start interacting with it.
                            self.uart = UART(self.device)

                            serialhandler._connected = True
                            logger.info('connection made now')
                            charline = ''

                            def handle_line(data):
                                serialhandler.raw_text = data
                                with serialhandler._recording_lock:
                                    if serialhandler._recording:
                                        logger.info("serialhandler._recording")
                                        serialhandler._record_file.write(data + "\n")

                                res = parse_any_line(data)

                                if res is not None:
                                    self._queue.put(res)

                            while self.device.is_connected: 
                                if self.uart is not None: 
                                    newdata=self.uart.read(timeout_sec=1)
                                    if newdata is not None:
                                        characters = newdata.decode()
                                        if "\n" in characters:
                                            charline = charline+characters

                                            #print ('charline')
                                            #print (charline)

                                            handle_line(charline)
                                            charline = ''
                                        else: 
                                            charline = charline+characters
                        finally:
                            logger.info('device disconnecting')
                            try:
                                serialhandler._connected = False
                                print('changed state')
                                self.stoprequest.set()
                                self.device.disconnect()
                                print ('disconnected device')
                            except: 
                                print ('disconnecting problem')
                                          
                def close(self):
                    try: 
                        #UART.disconnect_devices()  
                        serialhandler._connected =False
                        self.stoprequest.set()
                        self.device.disconnect()
                        logger.info('connection lost')
                    except: 
                        print ('problem disconnecting the bluetooth')
                    # with serialhandler._connection_lock:
                    #     if serialhandler._reader_thread is self:
                    #         serialhandler._reader_thread = None
                    # self.stopper.set()

                def write(self,text):
                    if self.uart is not None: 
                        self.uart.write(text)
                    else: 
                        print ('there is no uart connected')

            if 'Bluetooth' in port_selection: 

                self._reader_thread = bleThread(self.ble,self._queue)
                self._reader_thread.daemon = True
                self._reader_thread.start() 

            else: 
                self._reader_thread = serial.threaded.ReaderThread(
                    ser,
                    LineReader
                )
                # start the reader thread
                self._reader_thread.start()
                self._reader_thread.connect()

    @property
    def recording(self):
        with self._recording_lock:
            return self._recording

    def start_recording(self):
        with self._recording_lock:
            print('recording started!!')
            timestr = time.strftime("%Y%m%d-%H%M%S")
            self._recording = True
            self._record_file = open('data_' + timestr + '.bin', 'a')

    def stop_recording(self):
        with self._recording_lock:
            print('recording stopped')
            self._recording = False
            self._record_file.close()
