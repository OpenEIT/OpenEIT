# Serial handler class.
import time
import threading
import logging
import serial
import serial.threaded
import uuid
import Adafruit_BluefruitLE
from Adafruit_BluefruitLE.services import UART



# Define service and characteristic UUIDs used by the UART service.
UART_SERVICE_UUID = uuid.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
TX_CHAR_UUID      = uuid.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')
RX_CHAR_UUID      = uuid.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')

logger = logging.getLogger(__name__)


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

class SerialHandler:

    def __init__(self, queue):
        self._connection_lock = threading.Lock()
        self._reader_thread = None
        self._queue = queue
        self._recording_lock = threading.Lock()
        self._recording = False
        self._record_file = None
  
        # so we can process line reading 
        self.ble_line = ''
        self.get_line_lock = 0 
        # Get the BLE provider for the current platform.
        self.ble = Adafruit_BluefruitLE.get_provider()

    def is_connected(self):
        with self._connection_lock:
            return self._reader_thread is not None

    def disconnect(self):
        with self._connection_lock:
            if self._reader_thread is None:
                return

            self._reader_thread.close()
            self._reader_thread = None

    def write(self, text):
        self._reader_thread.write(text.encode())

    def bleconnect(self):
        # Clear any cached data because both bluez and CoreBluetooth have issues with
        # caching data and it going stale.
        self.ble.clear_cached_data()

        # Get the first available BLE network adapter and make sure it's powered on.
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
            device = UART.find_device()
            if device is None:
                raise RuntimeError('Failed to find UART device!')
        finally:
            # Make sure scanning is stopped before exiting.
            adapter.stop_scan()

        print('Connecting to device...')
        device.connect()  # Will time out after 60 seconds, specify timeout_sec parameter
                          # to change the timeout.
        # Once connected do everything else in a try/finally to make sure the device
        # is disconnected when done.
        try:
            # Wait for service discovery to complete for the UART service.  Will
            # time out after 60 seconds (specify timeout_sec parameter to override).
            print('Discovering services...')
            UART.discover(device)

            # Once service discovery is complete create an instance of the service
            # and start interacting with it.
            uart = UART(device)

            return uart, device
            # dis = DeviceInformation(device)
            # Write a string to the TX characteristic.
            # uart.write('Hello world!\r\n')
            # print("Sent 'Hello world!' to the device.")
            # print (dir(device))
            def handle_line(data):
          
                b = data.decode() # change it to a string
                if 'magnitudes' in b: 
                    print ('packet start')
                    self.get_line_lock = 1

                with self._recording_lock:
                    if self._recording:
                        logger.info("this is within handle line serialhandler._recording")
                        self._record_file.write(line + "\n")

                if self.get_line_lock == 1:
                    self.ble_line = self.ble_line + b 
                    res = parse_ble_line(self.ble_line)
                    if res is not None:
                        self.ble_line = ''
                        self._queue.put(res)

                        device.disconnect()

            while device.is_connected: 
                # Now wait up to one minute to receive data from the device.
                newdata=uart.read(timeout_sec=1)
                handle_line(newdata)

        finally:
            print('device disconnecting')
            # dis = DeviceInformation(device)
            # Make sure device is disconnected on exit.
            device.disconnect()


    def connect(self, port_selection):
        with self._connection_lock:
            if self._reader_thread is not None:
                raise RuntimeError("serial already connected")

            print('connecting to: ', port_selection)
            serialhandler = self

            if 'Bluetooth' in port_selection:
                print ('Bluetooth Callback')
                # Initialize the BLE system.  MUST be called before other BLE calls!
                self.ble.initialize()
                serialhandler._connected = True
                # Start the mainloop to process BLE events, and run the provided function in
                # a background thread.  When the provided main function stops running, returns
                # an integer status code, or throws an error the program will exit.
                # print (dir(self.ble))
                # self.ble.run_mainloop_with(self.bleconnect)
                
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
                except serial.SerialException:
                    logger.error('Cannot connect to %s', port_selection)
                    raise

            # serialhandler = self

            class LineReader(serial.threaded.LineReader):

                TERMINATOR = b'\n'

                def connection_made(self, transport):
                    serialhandler._connected = True
                    super().connection_made(transport)
                    logger.info('connection made')

                def handle_line(self, line):
                    # XXX: we should not record the raw stream but the
                    # parsed data
                    with serialhandler._recording_lock:
                        if serialhandler._recording:
                            logger.info("this is within handle line serialhandler._recording")
                            serialhandler._record_file.write(line + "\n")

                    res = parse_line(line)
                
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

            class BLEReader(threading.Thread):

                def handle_line(self,data):
              
                    b = data.decode() # change it to a string
                    if 'magnitudes' in b: 
                        print ('packet start')
                        self.get_line_lock = 1

                    with self._recording_lock:
                        if self._recording:
                            logger.info("this is within handle line serialhandler._recording")
                            self._record_file.write(line + "\n")

                    if self.get_line_lock == 1:
                        self.ble_line = self.ble_line + b 
                        res = parse_ble_line(self.ble_line)
                        if res is not None:
                            self.ble_line = ''
                            self._queue.put(res)

                            device.disconnect()

                def runble(self,device,uart):
                    while device.is_connected: 
                        # Now wait up to one minute to receive data from the device.
                        newdata=uart.read(timeout_sec=1)
                        handle_line(newdata)


            if 'Bluetooth' in port_selection: 
                print('Bluetooth option')
                # 
                # separate out the connection from the line reader? 
                # 
                # self._reader_thread = threading.Thread(target=runble,args=[]device)
                # self._reader_thread.start()

                self._reader_thread = threading.Thread(target=self.ble.run_mainloop_with(self.bleconnect))
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
