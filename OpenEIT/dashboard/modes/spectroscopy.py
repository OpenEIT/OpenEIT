import logging
import os
import dash
from dash.dependencies import Output, Event
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
PLOT_REFRESH_INTERVAL = 1.0 * S_TO_MS

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
                # html.Link(
                #     rel='stylesheet',
                #     href='/static/bootstrap.min.css'
                # ),
                html.Div( [
                    html.Div( [
                    # the button controls      
                    dcc.Dropdown(
                        id='name-dropdown',
                        options=[{'label':name, 'value':name} for name in self.portnames],
                        placeholder = 'Select Port',
                        value = self.portnames[0]
                        ),
                    ], style={'width': '60%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    html.Button(children='Connect', id='connectbutton', type='submit'),
                    ], style={'width': '15%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    html.Button(children='Save Current Spectrum', id='savebutton', type='submit'),
                    ] , style={'width': '15%', 'display': 'inline-block','text-align': 'center'}),

                ], style={'width': '100%', 'display': 'inline-block'} ),

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
                    interval=PLOT_REFRESH_INTERVAL
                ),

                # html.Div([
                    # html.P(id='connectbuttoncall',children='connectbuttoncall'),
                #     html.P(id='savebuttoncall',children='savebuttoncall'),
                # ], style={'width': '100%', 'display': 'inline-block'})
            
            ] )      

        # @self.app.server.route('/static/<path:path>')
        # def static_file(path):
        #     static_folder = os.path.join(os.getcwd(), 'static')
        #     return send_from_directory(static_folder, path)

        @self.app.callback( 
            dash.dependencies.Output('savebutton', 'children'),
            [dash.dependencies.Input('savebutton', 'n_clicks')])
        def callback_dropdown(n_clicks):
            print ('savebutton callback')
            if n_clicks is not None:
                try: 
                    if self.recording == False:
                        print('start recording')
                        self.controller.start_recording()
                    else:
                        print ('stop recording')
                        self.controller.stop_recording()
                except: 
                    print('could not record')
                    self.recording = False 
            if self.recording is True: 
                return 'Stop Recording' 
            else:
                return 'Record'


        @self.app.callback(
            dash.dependencies.Output(component_id='connectbutton', component_property='children'),
            [dash.dependencies.Input(component_id='connectbutton', component_property='n_clicks'),
            dash.dependencies.Input(component_id='name-dropdown', component_property='value')]
        )
        def connect(n_clicks, dropdown_value):
            if n_clicks is not None:
                try: 
                    if self.connected == False:
                        print('connect')
                        self.controller.connect(str(dropdown_value))
                    else:
                        print('disconnect')
                        self.controller.disconnect()
                except: 
                    print('could not connect, is the device plugged in?')
                    self.connected = False 
            if self.connected is True: 
                return 'Disconnect' 
            else:
                return 'Connect'
     
        @self.app.callback(
            Output('live-update-spectrogram', 'figure'),
            events=[Event('interval-component', 'interval')])
        def update_graph_scatter():
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
                        title='Amplitude',
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


