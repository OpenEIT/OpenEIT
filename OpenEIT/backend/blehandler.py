# Serial handler class.
import time
import threading
import logging
import serial
import serial.threaded

# Bluetooth specific
import uuid
import Adafruit_BluefruitLE

logger = logging.getLogger(__name__)

# Enable debug output.
#logging.basicConfig(level=logging.DEBUG)

# Define service and characteristic UUIDs used by the UART service.
UART_SERVICE_UUID = uuid.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
# UART_SERVICE_UUID = uuid.UUID('f14afb4b-e6fb-4621-8ef1-ff5b0a17cc8e')


TX_CHAR_UUID      = uuid.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')
RX_CHAR_UUID      = uuid.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')

# Get the BLE provider for the current platform.
ble = Adafruit_BluefruitLE.get_provider()


def parse_line(line):
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


class BLEHandler:

    def __init__(self, queue):
        self._connection_lock = threading.Lock()
        self._reader_thread = None
        self._queue = queue
        self._recording_lock = threading.Lock()
        self._recording = False
        self._record_file = None

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

    def connect(self, port_selection):
        with self._connection_lock:
            if self._reader_thread is not None:
                raise RuntimeError("ble UART already connected")



            serialhandler = self


            class LineReader(serial.threaded.LineReader):

                TERMINATOR = b'\n'

                # Write a string to the TX characteristic.
                # print('Sending message to device...')
                # tx.write_value('Hello world!\r\n')

                # Function to receive RX characteristic changes.  Note that this will
                # be called on a different thread so be careful to make sure state that
                # the function changes is thread safe.  Use queue or other thread-safe
                # primitives to send data to other threads.


                def connection_made(self, transport):
                    serialhandler._connected = True
                    super().connection_made(transport)
                    logger.info('connection made')

                def handle_line(self, line):
                    print('Received: {0}'.format(data))
                    # XXX: we should not record the raw stream but the
                    # parsed data
                    with serialhandler._recording_lock:
                        if serialhandler._recording:
                            logger.info("this is within handle line serialhandler._recording")
                            serialhandler._record_file.write(line + "\n")

                    res = parse_line(line)
                    logger.info('this is within handle line here')

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

            # Turn on notification of RX characteristics using the callback above.
            print('Subscribing to RX characteristic changes...')
            rx.start_notify(handle_line)

            self._reader_thread = serial.threaded.ReaderThread(
                rx,
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
