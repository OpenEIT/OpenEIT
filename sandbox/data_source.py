import csv
import logging
import time
import threading
import serial
import os
import sys

from datetime import datetime
from serial.tools import list_ports

import numpy as np
from scipy import signal

# Logger
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)
_LOGGER.addHandler(logging.StreamHandler())

DATA_OUTPUT_DIR = 'data'
BUFFER_SIZE = 500
NSPERG = 256
DT_FORMAT = '%y-%m-%d %H:%M:%S.%f'

# Filter params
FILTER_ORDER = 1
SAMPLING_FREQUENCY = 25.0
FILTER_WINDOW_SIZE = 20
F_NYQUIST = 0.5 * SAMPLING_FREQUENCY

# FILTER_TYPE = 'band'
# START_FREQUENCY = 0.1
# STOP_FREQUENCY = 5.0
# CUTOFF = [START_FREQUENCY / F_NYQUIST, STOP_FREQUENCY / F_NYQUIST]

FILTER_TYPE = 'low'
CUTOFF_FREQUENCY = 3.0
CUTOFF = CUTOFF_FREQUENCY / F_NYQUIST


def _clean_value(value, value_history):
    if len(value_history) > 0:
        last_valid_value = value_history[-1]
    else:
        last_valid_value = None

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


def _format_timestamp_to_string(timestamp):
    """
    Input timestamp can be:
    - Epoch time or counter
    - Datetime
    """
    if type(timestamp) == datetime:
        return timestamp.strftime(DT_FORMAT)
    else:
        return str(timestamp)


def _read_string_timestamp(str_timestamp):
    """
    Input string timestamp can be:
    - Epoch time or counter (E.g. '250') --> can be cast to int
    - Formatted datetime (E.g. '2018-12-01 12:05:04') --> cannot be cast to int
    """
    try:
        timestamp = int(str_timestamp)
    except ValueError:
        timestamp = datetime.strptime(str_timestamp, DT_FORMAT)
    return timestamp


class DeviceNotFoundException(Exception):
    pass


class DataSource:
    """
    Data source.

    If an input file path is provided, the source will replay data from
    this file. Otherwise, it will scan COM ports for the OpenEIT board and will
    stream data from the board.

    The data can optionally be filtered and / or saved to CSV.

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

    def __init__(self, input_file=None, filter_data=False, to_csv=False):

        # Whether to read from the input file or from the OpenEIT board
        if input_file:
            self.input_file = open(input_file, 'r')
            self.csv_reader = csv.reader(self.input_file)
            _LOGGER.info('Replaying data from file: %s' % input_file)
        else:
            self.input_file = None
            self.csv_reader = None
            _LOGGER.info('Attempting to connect to OpenEIT board ...')
        self.canned_data_interval = 1/SAMPLING_FREQUENCY

        # Filtered data
        self.filter_data = filter_data
        self.a, self.b = signal.butter(FILTER_ORDER, CUTOFF, btype=FILTER_TYPE)
        self.y_filtered = []
        self.sliding_window = np.zeros(FILTER_WINDOW_SIZE)  # Window to filter

        # Whether to save raw data to file
        self.to_csv = to_csv
        if to_csv:
            if not os.path.exists(DATA_OUTPUT_DIR):
                os.makedirs(DATA_OUTPUT_DIR)
            now = datetime.now().strftime('%y-%m-%d %H:%M:%S')
            output_path = os.path.join(DATA_OUTPUT_DIR, 'output - %s.csv' % now)
            if os.path.exists(output_path):
                raise FileExistsError('File already exists. '
                                      'Rename or delete: %s' % output_path)
            else:
                self.output_file = open(output_path, 'w')
                self.csv_writer = csv.writer(self.output_file)
                _LOGGER.info('Saving data to: %s' % output_path)
        else:
            self.output_file = None
            self.csv_writer = None

        # Board
        self.serial = None

        # Stats
        self.nb_points = 0
        self.start_time = None

        # Time series
        self.buffer_size = BUFFER_SIZE
        self.x = []
        self.y = []

        # PSD
        self.freqs = []
        self.psd = []

        # Threading
        self.run_event = threading.Event()
        self.thread = None

    def _connect_to_serial(self):
        ports = [p[0] for p in list_ports.comports()]
        valid_ports = [p for p in ports if 'usbserial' in p or 'usbmodem' in p]
        if len(valid_ports) > 0:
            port = valid_ports[0]
            baud_rate = 115200
            self.serial = serial.Serial(port, baud_rate)
        else:
            raise DeviceNotFoundException("OpenEIT board not found.")

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

        if not self.input_file:
            self._connect_to_serial()

        if not self.start_time:
            self.start_time = time.time()

        while self.run_event.is_set():
            self.nb_points += 1

            # Update y
            if self.serial and not self.input_file:
                t = datetime.now()
                value = self.serial.readline()
                _LOGGER.debug({'value': value})
            else:
                try:
                    row = self.csv_reader.__next__()
                except StopIteration:
                    _LOGGER.info('Done replaying canned data.')
                    sys.exit(1)
                t = _read_string_timestamp(row[0])
                value = float(row[1])
                time.sleep(self.canned_data_interval)

            value = _clean_value(value, self.y)
            if value:
                self.y.append(value)
                if len(self.y) > self.buffer_size:
                    self.y.pop(0)

                # write to csv
                if self.output_file:
                    timestamp = _format_timestamp_to_string(t)
                    output_row = [timestamp, value]
                    self.csv_writer.writerow(output_row)

                # Update sliding window
                new_window = np.append(self.sliding_window[1:], value)
                self.sliding_window = new_window

                # Update y_filtered
                if self.filter_data:
                    results = signal.lfilter(self.a, self.b, self.sliding_window)
                    result = results[-1]
                    self.y_filtered.append(result)
                    if len(self.y_filtered) > self.buffer_size:
                        self.y_filtered.pop(0)

                # Update PSD
                nsperg = NSPERG
                if len(self.y) < NSPERG:
                    nsperg = len(self.y)
                self.freqs, self.psd = signal.welch(self.y,
                                                    nperseg=nsperg,
                                                    fs=SAMPLING_FREQUENCY)

                # Update x
                self.x.append(t)
                if len(self.x) > self.buffer_size:
                    self.x.pop(0)

                # Log some stats about the data
                self._log_stats()

    def start(self):
        self.run_event.set()
        self.thread = threading.Thread(target=self._start)
        self.thread.start()

    def stop(self):
        if self.input_file:
            self.input_file.close()
        if self.output_file:
            self.output_file.close()
        self.run_event.clear()
        if self.thread:
            self.thread.join()
