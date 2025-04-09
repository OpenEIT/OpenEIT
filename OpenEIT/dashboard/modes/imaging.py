"""

# Copyright (c) Mindseye Biomedical LLC. All rights reserved.
# Distributed under the (new) CC BY-NC-SA 4.0 License. See LICENSE.txt for more info.

"""
import logging
import os
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
# import plotly.plotly as py
import plotly as py
from plotly.graph_objs import *
import plotly.graph_objs as go
import plotly.figure_factory as FF
import matplotlib.cm as cm
from flask import send_from_directory
import serial.tools.list_ports
import OpenEIT.dashboard
import queue
import numpy as np
import base64
#import io
#import decimal 
from plotly import exceptions, optional_imports
import plotly.colors as clrs
from plotly.graph_objs import graph_objs

PORT    = 8050
S_TO_MS = 1000
PLOT_REFRESH_INTERVAL = 0.5 * S_TO_MS

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
        # self.rsvaluemin = self.vmin
        # self.rsvaluemax = self.vmax
        self.run_file = False 

        self.n_electrodes = ['8','16','32']
        self.algorithms   = ['jac','bp','greit']
        self.img = None

    # Get's new data off the serial port. 
    def process_data(self):
        try:
            self.img = self.controller.image_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            logger.info("rendering new image ...")

    def set_baseline(self):
        print ('setting the baseline')
        self.controller.baseline()

    def run_file(self):
        self.run_file = True
        # this should be a bool so that self. controller.step_file is called every update interval. 
        # self.controller.step_file()

    def map_z2color(self,zval, colormap, vmin, vmax):
        #map the normalized value zval to a corresponding color in the colormap

        if vmin>vmax:
            raise ValueError('incorrect relation between vmin and vmax')
        t=(zval-vmin)/float((vmax-vmin))#normalize val
        R, G, B, alpha=colormap(t)
        return 'rgb('+'{:d}'.format(int(R*255+0.5))+','+'{:d}'.format(int(G*255+0.5))+\
               ','+'{:d}'.format(int(B*255+0.5))+')'

    def tri_indices(self,simplices):
        #simplices is a numpy array defining the simplices of the triangularization
        #returns the lists of indices i, j, k

        return ([triplet[c] for triplet in simplices] for c in range(3))

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
                            html.Div( [
                            html.P('Algorithm Settings: '),    
                            ], style={'width': '50%', 'display': 'inline-block','text-align': 'center'} ),

                            html.Div( [
                            html.Ul(id="algorithm_setting"),
                            ], style={'width': '20%', 'display': 'inline-block','text-align': 'center'} ),

                        ], style={'width': '70%', 'display': 'inline-block'} ),

                        html.Div( [
                            html.Div( [

                            dcc.Dropdown(
                                id='algorithm-dropdown',
                                options=[{'label':name, 'value':name} for name in self.algorithms],
                                placeholder = 'Select Algorithm',
                                value = self.controller._algorithm,
                                ),
                            ], className='btn-group',style={'width': '40%', 'display': 'inline-block','text-align': 'center'} ),

                            html.Div( [
                            dcc.Dropdown(
                                id='electrode-dropdown',
                                options=[{'label':name, 'value':name} for name in self.n_electrodes],
                                placeholder = 'Select Algorithm',
                                value = str(self.controller._n_el),
                                ),
                            ], className='btn-group',style={'width': '30%', 'display': 'inline-block','text-align': 'center'} ),

                            html.Div( [
                            html.Button(children='Set', id='setmode', type='submit',className ='btn btn-outline-dark'),
                            ], className='btn-group',style={'width': '20%', 'display': 'inline-block','text-align': 'center'} ),

                        ], style={'width': '70%', 'display': 'inline-block'} ),

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
                        interval=PLOT_REFRESH_INTERVAL,
                        n_intervals=0
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
###
        @self.app.callback(
            dash.dependencies.Output('algorithm_setting', 'children'),
            [dash.dependencies.Input('algorithm-dropdown', 'value'),
            dash.dependencies.Input('electrode-dropdown', 'value'),
            dash.dependencies.Input('setmode', 'n_clicks')
            ], )
        def update_output(selected_algorithm,selected_electrodes,n_clicks):
            if n_clicks is None:            
                c = self.controller.serial_getmode()
                selected_algorithm = self.controller.algorithm
                if 'c' in c:
                    print ('8 electrode mode')
                    selected_electrodes = '8'
                elif 'd' in c:
                    print ('16 electrode mode')
                    selected_electrodes = '16'
                elif 'e' in c:
                    print ('32 electrode mode')
                    selected_electrodes = '32'
                else: 
                    selected_electrodes = '- non-imaging mode'

            if n_clicks is not None:
                # this is getting called whenever we load it, which is a mistake. 
                print(selected_algorithm)
                print(selected_electrodes)

                # change the setting in firmware. 
                if self.connected: 
                    if int(selected_electrodes) == 8: 
                        value = 'c'
                    elif int(selected_electrodes) == 16: 
                        value = 'd'
                    else: # 32 electrodes
                        value = 'e'
                    data_to_send = str(value) + '\n'
                    self.controller.serial_write(data_to_send,selected_algorithm)

                self.algorithm  = selected_algorithm
                self.n_el       = int(selected_electrodes)
                # if the algorithm setting is change, we need to re-initialize the whole thing. 
                if self.algorithm  == 'greit':
                    self.gx,self.gy,self.ds = self.controller.greit_params()
                    self.img = self.ds # np.zeros((32,32),dtype=float)
                else: 
                    self.x,self.y,self.tri,self.el_pos = self.controller.plot_params()
                    self.img = np.zeros(self.x.shape[0]) 

            return selected_algorithm+selected_electrodes

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
            Output('output-container-range-slider', 'children'),
            [Input('range-slider', 'value')])
        def update_output(value):
            print ('the the update value function')
            print (value)
            if value[0] > value[1]: 
                self.vmin = value[1]
                self.vmax = value[0] 
            else: 
                self.vmin = value[0]
                self.vmax = value[1]                

            return ('('+str(self.vmin)+','+str(self.vmax)+')') #format(value)

        @self.app.callback(
            Output('slider-container', 'children'),
            [Input('minimum_range', 'value'),
             Input('maximum_range', 'value')])
        def display_controls(datasource_1_value, datasource_2_value):
                # print ('display controls')
                # print (datasource_1_value, datasource_2_value) 
                therange = 0 
                if datasource_2_value is not None:
                    therange = int(datasource_2_value) - int(datasource_1_value)

                DYNAMIC_CONTROLS = {}

                step     = int(therange)//10
                if step == 0:
                    step = 1

                DYNAMIC_CONTROLS = dcc.RangeSlider(
                    id    = 'range-slider',
                    marks= {i: ' {}'.format(i) for i in range(int(datasource_1_value), int(datasource_2_value),step)},
                    min   = datasource_1_value,
                    max   = datasource_2_value,
                    step  = therange//20,
                    value = [((int(datasource_2_value) - 5*therange)//10),((int(datasource_1_value) + therange)//10)]
                )
                return html.Div(
            DYNAMIC_CONTROLS
            )
        @self.app.callback(
            Output('live-update-image', 'figure'),
            [Input('interval-component', 'n_intervals')])
        def update_graph_scatter(n):
            # update the data queue. 
            if self.run_file is True: 
               if self.controller.step_file():
                  print ('stepped the file')
                  # self.process_data()
               else: 
                    self.run_file = False

            self.mode = self.controller.serial_getmode()
            if 'c' in self.mode or 'd' in self.mode or 'e' in self.mode: # and self.run_file is False:
                self.process_data()

            if self.algorithm  == 'greit':
                self.gx,self.gy,self.ds = self.controller.greit_params()

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
                         width=800,
                         height=800,
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

                if self.img is None or (len(self.el_pos) != self.controller.n_el):
                    self.x,self.y,self.tri,self.el_pos = self.controller.plot_params()
                    self.img = np.zeros(self.x.shape[0]) 
                    self.img[1] = 2.0

                if self.vmin >= self.vmax: 
                    self.vmin = 0 
                    self.vmax = 1000

                simplices=self.tri
                colormap = cm.plasma # specify the colormap
                if len(self.img) == 0: 
                    self.img = np.zeros(self.x.shape[0]) 
                    self.img[1] = 2.0

                points3D = np.vstack((self.x,self.y,self.img)).T
                tri_vertices=map(lambda index: points3D[index], simplices)# vertices of the surface triangles     
                zmean=[np.mean(tri[:,2]) for tri in tri_vertices ]# mean values of z-coordinates of 
                                                                  #triangle vertices
                min_zmean=self.vmin #np.min(zmean)
                max_zmean=self.vmax #np.max(zmean)
                facecolor=[self.map_z2color(zz,  colormap, min_zmean, max_zmean) for zz in zmean]
                I,J,K=self.tri_indices(simplices)
                self.zoro = np.zeros(len(self.img))

                data = [
                    go.Mesh3d(x=self.x,y=self.y,z=self.zoro,facecolor = facecolor,i=I,j=J,k=K,name='')
                ]

            return {'data': data, 'layout': layout}

        @self.app.callback(
            Output('live-update-histogram', 'figure'),
            [Input('interval-component', 'n_intervals')])
        def update_graph_scatter(n):

            flatimg = [0,1,0]
            #data = [go.Histogram(x=flatimg)]
            if self.algorithm == 'greit':
                # print ('algorithm is greit')
                # self.gx,self.gy,self.ds = self.controller.greit_params()
                # self.img = self.ds 
                if self.img is None:
                    self.img = np.zeros((32,32),dtype=float)
                    nanless = self.img[~np.isnan(self.img)]
                    flatimg = (nanless).flatten()
                else: 
                    nanless = self.img[~np.isnan(self.img)]
                    flatimg = (nanless).flatten()
            else: 
                self.x,self.y,self.tri,self.el_pos = self.controller.plot_params()
                if self.img is not None:
                    flatness = np.array(self.img).ravel()
                    nanless = flatness[~np.isnan(flatness)]
                    flatimg = (nanless).flatten()

                else: 
                    print ('nothing to histogram yet')
                    flatimg = [0,1,0]
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

        def autoscale(): 
            print ('we are in the autoscale function')
            nanless = self.img[~np.isnan(self.img)]
            self.vmax= float(int(np.max(nanless)*100))/100.0
            self.vmin =float(int(np.min(nanless)*100))/100.0

            if self.vmax <= self.vmin: # safety value. 
                self.vmin = 0
                self.vmax = 1000 

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

