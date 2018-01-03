# Serial handler class.
import time
import threading
import logging

import serial
import serial.threaded

logger = logging.getLogger(__name__)


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


class Serialhandler:

    def __init__(self, queue):
        self._connection_lock = threading.Lock()
        self._reader_thread = None
        self._queue = queue

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

    def connect(self, port_selection, *, line_hook=None):
        with self._connection_lock:
            if self._reader_thread is not None:
                raise RuntimeError("serial already connected")

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

            serialhandler = self

            class LineReader(serial.threaded.LineReader):

                TERMINATOR = b'\n'

                def connection_made(self, transport):
                    serialhandler._connected = True
                    super().connection_made(transport)
                    logger.info('connection made')

                def handle_line(self, line):
                    if line_hook is not None:
                        line_hook(line)
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

            self._reader_thread = serial.threaded.ReaderThread(
                ser,
                LineReader
            )

        # start the reader thread
        self._reader_thread.start()
        self._reader_thread.connect()

    def record_toggle(self):

        if self.isRecording:
            print('stop it recording: ', len(self.b), len(self.recorded_bytes))
            timestr = time.strftime("%Y%m%d-%H%M%S")
            self.fid = open('data_' + timestr + '.bin', 'ab')
            self.fid.write(self.b)
            self.fid.close()
            self.isRecording = False
        else:
            print('start recording')
            self.isRecording = True
