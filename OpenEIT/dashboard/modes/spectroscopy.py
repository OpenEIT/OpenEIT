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

PORT = 8050
S_TO_MS = 1000
PLOT_REFRESH_INTERVAL = 0.5 * S_TO_MS

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
_LOGGER.addHandler(logging.StreamHandler())

# Suppress unnecessary debug / warning messages from Flask
os.environ['FLASK_ENV'] = 'development'
flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.INFO)

layout = html.Div([html.H5('Hello, world!')])

class BISgui(object):

    def __init__(self, controller, app):

        self.controller = controller
        self.app = app         
        self.controller.register(
            "recording_state_changed",
            self.on_record_state_changed
        )

        self.controller.register(
            "connection_state_changed",
            self.on_connection_state_changed
        )
        self.connected = False
        self.recording = False 
        self.currentport = ''
        full_ports = list(serial.tools.list_ports.comports())
        self.portnames  = [item[0] for item in full_ports]
        self.mode = self.controller.serial_getmode()
        print (self.mode)
        # b followed by \r gives bioimpedance spectroscopy data. 
        self.freqs = [200,500,800,1000,2000,5000,8000,10000,15000,20000,30000,40000,50000,60000,70000]
        self.psd   = [0,0,0,0,0,0,0,0,0,0,0,0,0,0] 
        self.data_dict = {}
        self.data_dict = dict(zip(self.freqs, self.psd))
        self.layout = []

    # Get's new data off the serial port. 
    def process_data(self):
        while not self.controller.data_queue.empty():
            f,amp = self.controller.data_queue.get()
            self.data_dict[f] = amp

        self.freqs = list(self.data_dict.keys())
        self.psd   = list(self.data_dict.values())

    def return_layout(self):
        self.layout = html.Div( [
                html.Link(
                    rel='stylesheet',
                    href='/static/bootstrap.min.css'
                ),

                # The graph. 
                dcc.Graph(
                    id='live-update-spectrogram',
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
     
        @self.app.callback(
            Output('live-update-spectrogram', 'figure'),
            [Input('interval-component', 'n_intervals')])
        def update_graph_scatter(n):
            self.mode = self.controller.serial_getmode()
            if 'b'in self.mode:
                # update the data queue. 
                self.process_data()

            if len(self.data_dict.keys()) > 0:
                trace1 = go.Scatter(
                    x=list(self.data_dict.keys()),
                    y=list(self.data_dict.values()),
                    mode='lines',
                    name='PSD',
                    line={'shape': 'spline'},
                    fill='tozeroy'
                )

                data = [trace1]

                layout = go.Layout(
                    # title='Bioimpedance Spectroscopy',
                    xaxis=dict(
                        title='Frequency (Hz)',
                        type='linear',
                        autorange=True
                    ),
                    yaxis=dict(
                        title='Amplitude (Ohms)',
                        autorange=True
                    )
                )

                return {'data': data, 'layout': layout}

        return self.layout

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


