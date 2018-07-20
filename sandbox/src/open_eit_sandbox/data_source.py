import logging
import time
import random
import threading
from datetime import datetime
import serial.tools.list_ports

import numpy as np
from scipy import signal

# Logger
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)
_LOGGER.addHandler(logging.StreamHandler())

# Filter params
FILTER_ORDER = 1
SAMPLING_FREQUENCY = 25.0
FILTER_WINDOW_SIZE = 20
F_NYQUIST = 0.5 * SAMPLING_FREQUENCY

# FILTER_TYPE = 'band'
# START_FREQUENCY = 2.0
# STOP_FREQUENCY = 100.0
# CUTOFF = [START_FREQUENCY / F_NYQUIST, STOP_FREQUENCY / F_NYQUIST]

FILTER_TYPE = 'low'
CUTOFF_FREQUENCY = 2.0
CUTOFF = CUTOFF_FREQUENCY / F_NYQUIST


def _cleanup(value, last_valid_value):
    if value:
        try:
            value = float(value)
        except ValueError:
            value = last_valid_value
            _LOGGER.debug('Skipping value: %s' % value)
    else:
        value = last_valid_value
        _LOGGER.debug('No serial data')
    return value


class DataSource:
    """
    Data acquisition.

    Usage:

        source = DataSource()
        source.start()

        # Buffered data size
        print(source.buffer_size)

        # Plot buffered data
        plt.plot(source.x, source.y)

        # Plot filtered buffered data (if filtered_data was enabled)
        plt.plot(source.x, source.y_filtered)

    """

    def __init__(self, mock=False, filter_data=False):

        self.mock = mock
        self.filter_data = filter_data

        self.nb_points = 0
        self.start_time = None
        self.serial = None

        self.x = [datetime.now()]
        self.y = [0.0]
        self.y_filtered = [0.0]
        self.sliding_window = np.zeros(FILTER_WINDOW_SIZE)  # Window to filter

        self.run_event = threading.Event()
        self.thread = None

        self.buffer_size = 250
        self.mock_data_interval = 0.1
        self.a, self.b = signal.butter(FILTER_ORDER, CUTOFF, btype=FILTER_TYPE)

    def _connect_to_serial(self):
        ports = list(serial.tools.list_ports.comports())
        port = [p[0] for p in ports if 'usbserial' or 'usbmodem' in p[0]][0]
        baud_rate = 115200
        self.serial = serial.Serial(port, baud_rate)

    def _log_stats(self):
        elapsed_time = time.time() - self.start_time
        sampling_rate = self.nb_points / elapsed_time
        stats = {
            'elapsed_time': elapsed_time,
            'nb_points': self.nb_points,
            'sampling_rate': sampling_rate
        }
        _LOGGER.debug(stats)

    def _start(self):

        if not self.mock:
            self._connect_to_serial()

        if not self.start_time:
            self.start_time = time.time()

        while self.run_event.is_set():
            self.nb_points += 1

            # Update x
            self.x.append(datetime.now())
            if len(self.x) > self.buffer_size:
                self.x.pop(0)

            # Update y
            if self.serial and not self.mock:
                value = self.serial.readline()
            else:
                value = random.random()
                time.sleep(self.mock_data_interval)
            value = _cleanup(value, self.y[-1])
            self.y.append(value)
            if len(self.y) > self.buffer_size:
                self.y.pop(0)

            # Update y_filtered
            if self.filter_data:
                new_window = np.append(self.sliding_window[1:], value)
                self.sliding_window = new_window
                result = signal.lfilter(self.a, self.b, self.sliding_window)
            else:
                result = 0.0
            self.y_filtered.append(result[-1])
            if len(self.y_filtered) > self.buffer_size:
                self.y_filtered.pop(0)

            # Log some stats about the data
            self._log_stats()

    def start(self):
        self.run_event.set()
        self.thread = threading.Thread(target=self._start)
        self.thread.start()

    def stop(self):
        self.run_event.clear()
        if self.thread:
            self.thread.join()
