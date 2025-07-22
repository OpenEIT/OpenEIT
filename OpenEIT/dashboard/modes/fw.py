"""

# Copyright (c) Mindseye Biomedical LLC. All rights reserved.
# Distributed under the (new) CC BY-NC-SA 4.0 License. See LICENSE.txt for more info.

"""
import logging
import os
import dash
from dash.dependencies import Output,Input,State
import dash_core_components as dcc
import dash_html_components as html
# import plotly.plotly as py
import plotly as py
import plotly.graph_objs as go
from flask import send_from_directory
import serial.tools.list_ports
import OpenEIT.dashboard
import queue

# TODO: It would be nice to livestream the data from the serial port here. 

PORT = 8050
S_TO_MS = 1000
PLOT_REFRESH_INTERVAL = 1.0 * S_TO_MS
#PLOT_REFRESH_INTERVAL = 1000.0 * S_TO_MS

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
_LOGGER.addHandler(logging.StreamHandler())

# Suppress unnecessary debug / warning messages from Flask
os.environ['FLASK_ENV'] = 'development'
flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.ERROR)

layout = html.Div([html.H5('Hello, world!')])

class FWgui(object):

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

        sep = ' '
        #rest = str(full_ports[-1]).split(sep, 1)[0]
        if len(full_ports) > 0:
            rest = str(full_ports[-1]).split(sep, 1)[0]
        else:
            rest = 'none'

        self.currentport = rest

        self.controller.setportname(self.currentport)
        self.data = ''
        self.layout = []

    # Get's new data off the serial port. 
    def process_data(self):
        while not self.controller.data_queue.empty():
            self.data = self.controller.data_queue.get()
            #self.data_dict[f] = amp

    def return_layout(self):
        full_ports = list(serial.tools.list_ports.comports())
        self.portnames  = [item[0] for item in full_ports]
        self.currentport = self.controller.getportname()
        #print (self.currentport)

        self.layout = html.Div( [
                html.Link(
                    rel='stylesheet',
                    href='/static/bootstrap.min.css'
                ),
                html.Div( [
                    html.Div( [
                    # the button controls      
                    dcc.Dropdown(
                        id='name-dropdownfw',
                        options=[{'label':name, 'value':name} for name in self.portnames],
                        #placeholder = 'hello',
                        value = self.currentport,
                        clearable=False
                        ),
                    ], className='btn-group',style={'width': '40%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    html.Button(children='Connect', id='connectbuttonfw', type='submit',className ='btn btn-outline-dark'),
                    ], className='btn-group',style={'width': '20%', 'display': 'inline-block','text-align': 'center'} ),
   
                ], style={'width': '100%', 'display': 'inline-block'} ),

                html.P(''),

                html.Div( [
                    # the button controls      
                    html.Div( [
                    dcc.Input(
                        id='send_data',
                        placeholder='Enter',
                        type='text',
                        value='d'
                    ),
                    ], style={'width': '20%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    html.Button(children='Send', id='send', type='submit',className ='btn btn-outline-dark'),
                    ], style={'width': '20%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    html.Ul(id="datasent"),
                    ], style={'width': '20%', 'display': 'inline-block','text-align': 'center'} ),

                
                ], style={'width': '100%', 'display': 'inline-block'} ),

                html.Div( [
                    html.Ul(id="current_mode"),
                ], style={'width': '100%', 'display': 'inline-block','text-align': 'center'} ),

                html.P(''),

                dcc.Textarea(
                    id ='textarea', 
                    #placeholder='',
                    value='string',
                    contentEditable = False,
                    #disabled = True,
                    maxLength = 500,
                    readOnly = True,
                    rows = 10,
                    style={'width': '60%'}
                ),
                html.P('a:Time Series, b: Bioimpedance Spectroscopy, c: 8 electrode EIT, d: 16 electrode EIT, e: 32 electrode EIT'),
                dcc.Interval(
                    id='interval-component',
                    interval=PLOT_REFRESH_INTERVAL,
                    n_intervals=0
                ),

            ] )     

        @self.app.callback(
            Output('textarea', 'value'),
            [Input('interval-component', 'n_intervals')])
        def update_textbox(n):
            return self.controller.return_line()

        @self.app.callback(
            Output('datasent', 'children'),
            [Input('send', 'n_clicks'),
            Input('send_data', 'value')]
            )    
        def senddata(n_clicks,value):
            if n_clicks is not None:
                if self.connected: 
                    data_to_send = str(value) + '\n'
                    self.controller.serial_write(data_to_send)
                    #print (data_to_send)
                    
                    return data_to_send

            return 'connect to send data'

        @self.app.callback(
            Output('current_mode', 'children'),
            [Input('interval-component', 'n_intervals')])   
        def mode(n):
            m = self.controller.serial_getmode()
            if 'a' in m:
                return 'time series mode'
            elif 'b' in m:
                return 'bioimpedance spectroscopy mode'
            elif 'c' in m:
                return '8 electrode imaging mode'
            elif 'd' in m:
                return '16 electrode imaging mode'   
            elif 'e' in m:
                return '32 electrode imaging mode'                                                 
            else: 
                return 'another mode'         

        @self.app.callback(
            Output(component_id='connectbuttonfw', component_property='children'),
            [Input(component_id='connectbuttonfw', component_property='n_clicks'),
            Input(component_id='name-dropdownfw', component_property='value')]
        )
        def connect(n_clicks, dropdown_value):
            if n_clicks is not None:
                try: 
                    if self.connected == False:
                        print(str(dropdown_value))                     
                        self.controller.connect(str(dropdown_value))
                        return 'Disconnect' 
                    else:
                        print('disconnect')
                        self.controller.disconnect()
                        return 'Connect'
                except: 
                    print ('problem')
            if self.connected is True: 
                return 'Disconnect' 
            else:
                return 'Connect'
     
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


