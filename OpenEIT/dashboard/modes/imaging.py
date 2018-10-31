import logging
import os
import dash
from dash.dependencies import Input, Output, Event, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.plotly as py
from plotly.graph_objs import *
import plotly.graph_objs as go
import plotly.figure_factory as FF
import matplotlib.cm as cm
from flask import send_from_directory
import serial.tools.list_ports
import OpenEIT.dashboard
import queue
import numpy

import base64
#import io

PORT = 8050
S_TO_MS = 1000
PLOT_REFRESH_INTERVAL = 1.0 * S_TO_MS

# _LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel(logging.DEBUG)
# _LOGGER.addHandler(logging.StreamHandler())

logger = logging.getLogger(__name__)

layout = html.Div([html.H5('Hello, world!')])
# Suppress unnecessary debug / warning messages from Flask
os.environ['FLASK_ENV'] = 'development'
flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.INFO)

class Tomogui(object):

    def __init__(self, controller, app):

        self.controller = controller
        self.app= app 

        self.n_el = self.controller.n_el
        self.algorithm = self.controller.algorithm

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

        self.vmin = 0 
        self.vmax = 1000

        self.mode = self.controller.serial_getmode()

        self.rsvaluemin = self.vmin
        self.rsvaluemax = self.vmax

        self.run_file = False 

        if self.algorithm  == 'greit':
            self.gx,self.gy,self.ds = self.controller.greit_params()
            self.img = self.ds # numpy.zeros((32,32),dtype=float)
        else: 
            self.x,self.y,self.tri,self.el_pos = self.controller.plot_params()
            self.img = numpy.zeros(self.x.shape[0]) 

    # Get's new data off the serial port. 
    def process_data(self):

        try:
            self.img = self.controller.image_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            logger.info("rendering new image ...")

    def dist_origin(self,x, y, z):
        return z

    def set_baseline(self):
        print ('setting the baseline')
        self.controller.baseline()

    def run_file(self):
        self.run_file = True
        # this should be a bool so that self. controller.step_file is called every update interval. 
        # self.controller.step_file()

    def return_layout(self):

        self.layout = html.Div( [
                # stylesheet. 
                html.Link(
                    rel='stylesheet',
                    href='/static/bootstrap.min.css'
                ),


                html.Div( [  

                    # The histogram and controls part: 
                    html.Div( [
                        html.Div( [
                            html.P('Offline File Control: '),
                            # the offline controls 
                            html.Div( [
                 
                                dcc.Upload(id='readfromfile',children='Read File',className ='btn btn-outline-dark'),

                                html.Button(children='Step', id='stepfile', type='submit',className ='btn btn-outline-dark'),
               
                                html.Button(children='Step Back', id='stepback', type='submit',className ='btn btn-outline-dark'),
                      
                                html.Button(children='Run', id='runfile', type='submit',className ='btn btn-outline-dark'),
                  
                                html.Button(children='Reset', id='resetfilem', type='submit',className='btn btn-outline-dark'),
                
                            ], className='btn-group', style={'width': '100%', 'display': 'inline-block'} ),

                        ], style={'width': '100%', 'display': 'inline-block'} ),

                        html.Div( [
                
                            html.P('Realtime Control: '),
                  
                            html.Button(children='Baseline', id='baseline', type='submit',className ='btn btn-outline-dark'),
             
                            html.Button(children='Autoscale', id='autoscale', type='submit',className ='btn btn-outline-dark'),
                     
                            html.Div( [
                            html.Div(id='output-container-range-slider')
                            ], className='btn-group', style={'width': '100%', 'display': 'inline-block','text-align': 'center'} ),


                        ], className='btn-group',  style={'width': '100%', 'display': 'inline-block'} ),


                       html.Div(
                                id='slider-container',
                                style={'width': '100%', 'display': 'inline-block','text-align': 'center'}
                        ),
                        html.P(''),


                        ## insert sliders and things here:
                        html.Div( [

                            html.Div( [
                            html.P('Range Min: '),
                            ], style={'width': '20%', 'display': 'inline-block','text-align': 'center'} ),

                            html.Div( [
                            dcc.Input(
                                id='minimum_range',
                                placeholder='Enter',
                                style={'width': 80},
                                type='number',
                                value='0'
                            ),
                            ], style={'width': '20%', 'display': 'inline-block','text-align': 'center'} ),

                     
                            html.Div( [
                                html.P('Range Max: '),
                            ], style={'width': '20%', 'display': 'inline-block','text-align': 'center'} ),

                            html.Div( [
                            dcc.Input(
                                id='maximum_range',
                                placeholder='Enter',
                                type='number',
                                style={'width': 80},
                                value='1000'
                            ),
                            ] , style={'width': '20%', 'display': 'inline-block','text-align': 'center'}), 
                         
                        ], style={'width': '100%', 'display': 'inline-block'} ),
                        
                        html.Div( [
                        dcc.Graph(
                            id='live-update-histogram',
                            animate=False,
                            config={
                                'displayModeBar': False
                            }
                                ),
                        ], style={'width': '100%', 'display': 'inline-block','text-align': 'center'} ),


                    ], style={'width': '40%', 'display': 'inline-block','text-align': 'center'} ),


                    html.Div( [
                        # The big image graph. 
                        dcc.Graph(
                            id='live-update-image',
                            animate=False,
                            config={
                                'displayModeBar': False
                            }
                        ),
                        dcc.Interval(
                        id='interval-component',
                        interval=PLOT_REFRESH_INTERVAL
                    ),
                    ] , style={'width': '50%', 'display': 'inline-block','text-align': 'center'}), 


                ], style={'width': '100%', 'display': 'inline-block'} ),

                html.Ul(id="afilelist",style={'display': 'none'}),
                html.Ul(id="astepfile"),
                html.Ul(id="astepback"),
                html.Ul(id="arunfile"),
                html.Ul(id="aresetfilem"),
                html.Ul(id="abaseline"),
                html.Ul(id="aautoscale"),
                html.Ul(id="a"),
                html.Ul(id="ab"),
            ] )      

        @self.app.callback(Output("afilelist", "children"),
               [Input('readfromfile', 'contents')],
              [State('readfromfile', 'filename'),
               State('readfromfile', 'last_modified')])       
        def readfile_output(contents, filename, date):
            if filename is not None:
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                self.controller.load_file(filename,decoded)
                self.run_file = False
                return 'file loaded'
            else: 
                return 'no file'

        @self.app.callback(
                    Output("astepfile", "children"),
                    [Input("stepfile", "n_clicks")], )
        def step_call(n_clicks):
            if n_clicks is not None:
                print ('step forward')
                self.controller.step_file()
                self.run_file = False
                return 'step'
            else: 
                return 'not step'

        @self.app.callback(
                    Output("astepback", "children"),
                    [Input("stepback", "n_clicks")], )
        def stepback_call(n_clicks):
            if n_clicks is not None:
                print ('step back')
                self.controller.step_file_back()
                self.run_file = False
                return 'step back'
            else: 
                return 'not step back'

        @self.app.callback(
                    Output("arunfile", "children"),
                    [Input("runfile", "n_clicks")], )
        def runfile(n_clicks):
            if n_clicks is not None:
                self.run_file = True
                return 'runfile'
            else: 
                return 'not runfile'

        @self.app.callback(
                    Output("aresetfilem", "children"),
                    [Input("resetfilem", "n_clicks")], )
        def resetfilemarker(n_clicks):
            if n_clicks is not None:
                self.controller.reset_file()  
                self.run_file = False
                return 'reset filem'
            else: 
                return 'reset not'   

        @self.app.callback(
                    Output("abaseline", "children"),
                    [Input("baseline", "n_clicks")], )
        def baseline_data(n_clicks):
            if n_clicks is not None:
                self.set_baseline()
                return 'baseline'
            else: 
                return 'not baseline'

        @self.app.callback(
                    Output("maximum_range", "value"),
                    [Input("autoscale", "n_clicks")], )
        def autoscale_data(n_clicks):
            if n_clicks is not None:
                autoscale()  
                return  self.vmax

        @self.app.callback(
                    Output("minimum_range", "value"),
                    [Input("autoscale", "n_clicks")], )
        def autoscale_data(n_clicks):
            if n_clicks is not None:
                autoscale()  
                return  self.vmin

        @self.app.callback(
                    Output("range-slider", "value"),
                    [Input("maximum_range", "value")], )
        def change_maxrange(value):
            self.rsvaluemax = value
            return value

        @self.app.callback(
                    Output("ab", "children"),
                    [Input("minimum_range", "value")], )
        def change_minrange(value):
            self.rsvaluemin = value
            return 'ab'

        @self.app.callback(
            Output('output-container-range-slider', 'children'),
            [Input('range-slider', 'value')])
        def update_output(value):
            # based on value, updated colorbar vmin and vmax. 
            self.vmin = value[0]
            self.vmax = value[1]
            return format(value)

        @self.app.callback(
            Output('slider-container', 'children'),
            [Input('minimum_range', 'value'),
             Input('maximum_range', 'value')])
        def display_controls(datasource_1_value, datasource_2_value):
                print (datasource_1_value, datasource_2_value) 
                DYNAMIC_CONTROLS = {}
                therange = int(datasource_2_value) - int(datasource_1_value)
                step     = int(therange)//10
                if step == 0:
                    step = 1

                DYNAMIC_CONTROLS = dcc.RangeSlider(
                    id    = 'range-slider',
                    marks= {i: ' {}'.format(i) for i in range(int(datasource_1_value), int(datasource_2_value),step)},
                    min   = datasource_1_value,
                    max   = datasource_2_value,
                    step  = therange//20,
                    value = [((int(datasource_1_value) + therange)//10),((int(datasource_2_value) - 5*therange)//10)]
                )
                return html.Div(
            DYNAMIC_CONTROLS
            )
        @self.app.callback(
            Output('live-update-image', 'figure'),
            events=[Event('interval-component', 'interval')])
        def update_graph_scatter():
            # update the data queue. 
            if self.run_file is True: 
               if self.controller.step_file():
                  print ('stepped the file')
                  # self.process_data()
               else: 
                    self.run_file = False

            if self.mode == 'c': # and self.run_file is False:
                # print ('processed the data')
                # if there is data on the queue, do an update. 
                self.process_data()

            if self.algorithm  == 'greit':
                self.gx,self.gy,self.ds = self.controller.greit_params()
                print (self.img)
                #self.img = self.ds # numpy.zeros((32,32),dtype=float)
                # If algorithm is GREIT 
                layout = go.Layout(
                    width = 500,
                    height = 500,
                    # title = "EIT reconstruction",
                    xaxis = dict(
                      #nticks = 10,
                      domain = [0.0, 0.0],
                      showgrid=False,
                      zeroline=False,
                      showline=False,
                      ticks='',
                      showticklabels=False,
                      # autorange = 'reversed',
                      # title='EIT',
                    ),
                    yaxis = dict(
                      scaleanchor = "x",
                      domain = [0, 0.0],
                      showgrid=False,
                      zeroline=False,
                      showline=False,
                      ticks='',
                      showticklabels=False,
                      # autorange = 'reversed',
                    ),
                    showlegend= False
                )

                data = [
                    go.Heatmap(
                        z=self.img,
                        colorscale='Jet',
                        zmin=self.vmin, zmax=self.vmax,
                        colorbar=dict(
                                #title='Colorbar',
                                lenmode = 'fraction',
                                len = 1.0,
                                x=1.2,
                                y = 0.5
                            ),
                    )
                ]
            else: 
                self.x,self.y,self.tri,self.el_pos = self.controller.plot_params()
                #self.img = numpy.zeros(self.x.shape[0])
                # print (self.img)

                camera = dict(
                    up=dict(x=0, y=0, z=1),
                    center=dict(x=0, y=0, z=0),
                    eye=dict(x=0.0, y=0.0, z=2.5)
                )


                noaxis=dict(showbackground=False,
                            showline=False,
                            zeroline=False,
                            showgrid=False,
                            showticklabels=False,
                            title=''
                          )

                layout = go.Layout(
                         width=400,
                         height=400,
                         scene=dict(
                            xaxis=noaxis,
                            yaxis=noaxis,
                            zaxis=noaxis,
                            aspectratio=dict(
                                x=1.0,
                                y=1.0,
                                z=0.0),
                            camera =camera,
                            )

                        )
                self.img[1] = 2.0
                data = FF.create_trisurf(x=self.x, y=self.y, z=self.img,
                                         simplices=self.tri,
                                         color_func=self.dist_origin, # this is equivalent to the mask in tripcolor. 
                                         colormap='Portland',
                                         show_colorbar=False,
                                         title="Mesh Reconstruction",
                                         aspectratio=dict(x=1.0, y=1.0, z=0.01),
                                         showbackground=False,
                                         plot_edges=False,
                                         height=600, width=600, 
                                         scale=None,
                                         ) 

            return {'data': data, 'layout': layout}

        @self.app.callback(
            Output('live-update-histogram', 'figure'),
            events=[Event('interval-component', 'interval')])
        def update_graph_scatter():

            # print (self.img)

            nanless = self.img[~numpy.isnan(self.img)]
            flatimg = (nanless).flatten()

            data = [go.Histogram(x=flatimg)]

            layout = go.Layout(
                title='Histogram',
                width=500,
                height=300,
                xaxis=dict(
                    title='Amplitudes',
                    type='linear',
                    autorange=True
                ),
                yaxis=dict(
                    title='Frequency',
                    autorange=True
                )

            )

            return {'data': data, 'layout': layout}

        def autoscale(): # This sets baseline to what was originally stored in the background.txt file. 
            print ('we are in the autoscale function')
            nanless = self.img[~numpy.isnan(self.img)]
            self.vmax= float(int(numpy.max(nanless)*100))/100.0
            self.vmin =float(int(numpy.min(nanless)*100))/100.0


            self.rsvaluemin = self.vmin
            self.rsvaluemax = self.vmax
            display_controls(self.vmin,self.vmax)

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

