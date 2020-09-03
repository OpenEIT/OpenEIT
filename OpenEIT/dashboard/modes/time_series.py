"""

# Copyright (c) Mindseye Biomedical LLC. All rights reserved.
# Distributed under the (new) CC BY-NC-SA 4.0 License. See LICENSE.txt for more info.

"""
import logging
import os
import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly.plotly as py
import plotly.graph_objs as go
from flask import send_from_directory
import serial.tools.list_ports
import OpenEIT.dashboard
import queue
import time
from datetime import datetime, timedelta
import numpy as np
from scipy import signal

layout = html.Div([html.H5('Hello, world!')])

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
_LOGGER.addHandler(logging.StreamHandler())

PORT = 8050
S_TO_MS = 1000
PLOT_REFRESH_INTERVAL = 0.2 * S_TO_MS


DATA_OUTPUT_DIR = 'data'
BUFFER_SIZE = 500
NSPERG = 256
DT_FORMAT = '%y-%m-%d %H:%M:%S.%f'
# Filter params
FILTER_ORDER = 1
SAMPLING_FREQUENCY = 25.0
FILTER_WINDOW_SIZE = 20
F_NYQUIST = 0.5 * SAMPLING_FREQUENCY
FILTER_TYPE = 'low'
CUTOFF_FREQUENCY = 3.0
CUTOFF = CUTOFF_FREQUENCY / F_NYQUIST


# Suppress unnecessary debug / warning messages from Flask
os.environ['FLASK_ENV'] = 'development'
flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.INFO)



def _clean_value(value, value_history):

    if len(value_history) > 0:
        last_valid_value = value_history[-1]
    else:
        last_valid_value = 0 #None

    if value:
        try:
            value = value
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

class Timeseriesgui(object):

    def __init__(self,controller,app):

        self.controller = controller
        self.app 		= app 

        self.controller.register(
            "recording_state_changed",
            self.on_record_state_changed
        )

        self.controller.register(
            "connection_state_changed",
            self.on_connection_state_changed
        )
        self.connected      = False
        self.recording      = False 
        self.currentport    = ''
        full_ports          = list(serial.tools.list_ports.comports())
        self.portnames      = [item[0] for item in full_ports]
        self.mode = self.controller.serial_getmode()
        self.canned_data_interval = 1/SAMPLING_FREQUENCY
        self.tdelta = timedelta(seconds=self.canned_data_interval)
        # Filtered data True or False. 
        self.filter_data = True #filter_data
        self.a, self.b = signal.butter(FILTER_ORDER, CUTOFF, btype=FILTER_TYPE)
        self.y_filtered = []
        self.sliding_window = np.zeros(FILTER_WINDOW_SIZE)  # Window to filter
        # Stats
        self.nb_points = 0
        self.start_time = time.time()
        # Time series
        self.buffer_size = BUFFER_SIZE
        self.x = []
        self.y = []
        # PSD
        self.freqs = []
        self.psd = []

    def _log_stats(self):
        elapsed_time = time.time() - self.start_time
        sampling_rate = self.nb_points / elapsed_time
        stats = {
            'elapsed_time': elapsed_time,
            'nb_points': self.nb_points,
            'sampling_rate': sampling_rate
        }
        _LOGGER.debug(stats)

    # Get's new data off the serial port. 
    def process_data(self):
        y_batch = []
        # get data off the stack. 
        while not self.controller.data_queue.empty():
            y_batch = self.controller.data_queue.get()

        t       = datetime.now()
        value   = y_batch
    
        for i in range(len(y_batch)):
            value   = y_batch[i]
            t       = t + self.tdelta

            value = _clean_value(value,self.y)

            if value:
                #print ('v',len(self.y) )
                self.y.append(value)
                self.x.append(t)
                if len(self.y) > self.buffer_size:
                    self.y.pop(0)
                    self.x.pop(0)
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

        
        # Log some stats about the data
        #self._log_stats()     

    def return_layout(self):

        self.layout = html.Div( [
                html.Link(
                    rel='stylesheet',
                    href='/static/bootstrap.min.css'
                ),

                dcc.Graph(
                    id='live-update-time-series',
                    animate=False,
                    config={
                        'displayModeBar': False
                    }
                ),
                dcc.Graph(
                    id='live-update-psd',
                    animate=False,
                    config={
                        'displayModeBar': False
                    }
                ),
                dcc.Interval(
                    id='interval-component',
                    interval=PLOT_REFRESH_INTERVAL,
                    n_intervals=0
                ),

            ] )      
         
        @self.app.callback(Output('live-update-time-series', 'figure'),
                      [Input('interval-component', 'n_intervals')])
        def update_graph_scatter(n):
            self.mode = self.controller.serial_getmode()

            if 'a' in self.mode:
                # update from the data queue. 
                self.process_data()

            if len(self.x) > 0:
                trace1 = go.Scatter(
                    x=self.x,
                    y=self.y,
                    mode='lines',
                    name='Data',
                    # line={'shape': 'spline'}
                )

                data = [trace1]

                if len(self.y_filtered) > 0:
                    trace2 = go.Scatter(
                        x=self.x,
                        y=self.y_filtered,
                        mode='lines',
                        name='Filtered Data',
                        # line={'shape': 'spline'}
                    )
                    data.append(trace2)

                x_min = min(self.x)
                x_max = max(self.x)
                y_min = min(self.y)
                y_max = max(self.y)

                layout = go.Layout(
                    title='Time Series Data',
                    xaxis=dict(
                        title='Time',
                        range=[x_min, x_max]
                    ),
                    yaxis=dict(
                        title='Impedance (Ohms)',
                        range=[y_min, y_max]
                    ),

                )

                return {'data': data, 'layout': layout}

        @self.app.callback(Output('live-update-psd', 'figure'),
                      [Input('interval-component', 'n_intervals')])
        def update_graph_scatter(n):
            if len(self.x) > 0:
                trace1 = go.Scatter(
                    x=self.freqs,
                    y=self.psd,
                    mode='lines',
                    name='PSD',
                    line={'shape': 'spline'},
                    fill='tozeroy'
                )

                data = [trace1]

                layout = go.Layout(
                    title='Power Spectrum Density',
                    xaxis=dict(
                        title='Frequency (Hz) Log Scale',
                        type='log',
                        autorange=True
                    ),

                    yaxis=dict(
                        title='Power (dB)',
                        autorange=True
                    )
                )

                return {'data': data, 'layout': layout}
        
        return self.layout
        # _LOGGER.debug('App running at: http://localhost:%s' % PORT)
        # app.run_server(port=PORT)

    def on_connection_state_changed(self, connected):
        if connected:
            self.connected = True
        else:
            self.connected = False 

    def on_record_state_changed(self, recording):
        if recording:
            self.recording = True
        else:
            self.recording = False 


