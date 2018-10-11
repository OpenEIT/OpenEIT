import logging
import os
import dash
from dash.dependencies import Input, Output, Event
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



PORT = 8050
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
        self.app 		= app 

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

        # b followed by \r gives bioimpedance spectroscopy data. 
        # self.freqs = [200,500,800,1000,2000,5000,8000,10000,15000,20000,30000,40000,50000,60000,70000]
        # self.psd   = [0,0,0,0,0,0,0,0,0,0,0,0,0,0] 
        # self.data_dict = {}
        # self.data_dict = dict(zip(self.freqs, self.psd))

        self.vmin = 0 
        self.vmax = 1000

        self.range_min  = 0 
        self.range_max  = 1500
        self.range_step = 20

        self.rsvaluemin = 20
        self.rsvaluemax = 1100

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
            # before = time.time()
            # self.update_figure()
            # self.text = 'render time: %.2f' % (
            #     time.time() - before)
            # logger.info(self.text)

        # How do we check if the image has changed?     
        # self.img = 1.1*self.img     


    def dist_origin(self,x, y, z):
        return z

    def set_baseline(self):
        print ('setting the baseline')
        self.controller.baseline()

    def autoscale(self): # This sets baseline to what was originally stored in the background.txt file. 
        print ('we are in the autoscale function')
        nanless = self.img[~numpy.isnan(self.img)]
        self.vmax= float(int(numpy.max(nanless)*100))/100.0
        self.vmin =float(int(numpy.min(nanless)*100))/100.0

        # Update the range-slider parameters.
        # This doesn't work as the range-slider doesn't like being updated dynamically. 
        # 
        self.range_min  = self.vmin
        self.range_max  = self.vmax
        self.range_step = (self.vmax - self.vmin)/10.0
        # we also need to update the current range slider values. 

    def load_file(self,file_path):

        try:
            file_handle = open(file_path, "r")
            #logger.info(file_handle)
        except RuntimeError as err:
            logger.error('problem opening file dialog: %s', err)

        if file_handle is None:
            print ('didnt get the file!')
            return
        self.controller.load_file(file_handle)

    def run_file(self):
        self.run_file = True
        # this should be a bool so that self. controller.step_file is called every update interval. 
        # self.controller.step_file()

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

    def return_layout(self):

        self.layout = html.Div( [
                html.Div( [

                    html.Div( [
                        html.P('Realtime Control: '),
                    ], style={'width': '10%', 'display': 'inline-block','text-align': 'center'} ),
                    

                    html.Div( [
                    # the button controls      
                    dcc.Dropdown(
                        id='name-dropdownim',
                        options=[{'label':name, 'value':name} for name in self.portnames],
                        placeholder = 'Select Port',
                        value = self.portnames[0]
                        ),
                    ], style={'width': '30%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    html.Button(children='Connect', id='connectbuttonim', type='submit'),
                    ], style={'width': '10%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    html.Button(children='Save Current Spectrum', id='savebuttonim', type='submit'),
                    ] , style={'width': '10%', 'display': 'inline-block','text-align': 'center'}),

                    html.Div( [
                    html.Button(children='Baseline', id='baseline', type='submit'),
                    ] , style={'width': '10%', 'display': 'inline-block','text-align': 'center'}),

                    html.Div( [
                    html.Button(children='Autoscale', id='autoscale', type='submit'),
                    ] , style={'width': '15%', 'display': 'inline-block','text-align': 'center'}),

                    # html.Div( [
                    # html.Button(children='Update Histogram', id='histogram', type='submit'),
                    # ] , style={'width': '15%', 'display': 'inline-block','text-align': 'center'}),

                ], style={'width': '100%', 'display': 'inline-block'} ),

                html.Div( [
                                        # the button controls      
                    html.Div( [
                    html.P('Offline File Control: '),
                    ], className='btn-group',style={'width': '15%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    dcc.Upload(id='readfromfile',children=html.Button('Read File',id='rbut')),
                    ] , style={'width': '10%', 'display': 'inline-block','text-align': 'center'}),
                    
                    html.Div( [
                    html.Button(children='Step', id='stepfile', type='submit'),
                    ], style={'width': '10%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    html.Button(children='Step Back', id='stepback', type='submit'),
                    ] , style={'width': '10%', 'display': 'inline-block','text-align': 'center'}),

                    html.Div( [
                    html.Button(children='Run', id='runfile', type='submit'),
                    ] , style={'width': '10%', 'display': 'inline-block','text-align': 'center'}),

                    html.Div( [
                    html.Button(children='Reset File Marker', id='resetfilem', type='submit'),
                    ] , style={'width': '10%', 'display': 'inline-block','text-align': 'center'}),                    

                ], style={'width': '100%', 'display': 'inline-block'} ),


                html.Div( [

                    html.Div( [
                    html.P('Range Min: '),
                    ], style={'width': '10%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    dcc.Input(
                        id='minimum_range',
                        placeholder='Enter',
                        type='text',
                        value=''
                    ),
                    ] , style={'width': '10%', 'display': 'inline-block','text-align': 'center'}), 

                    html.Div(
                     [
                        dcc.RangeSlider(
                            id='range-slider',
                            count=1,
                            min=self.range_min,
                            max=self.range_max,
                            step=self.range_step,
                            value=[self.rsvaluemin, self.rsvaluemax]
                        ),
                    ] , style={'width': '60%', 'display': 'inline-block','text-align': 'center'}),                     

                    html.Div( [
                        html.P('Range Max: '),
                    ], style={'width': '10%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    dcc.Input(
                        id='maximum_range',
                        placeholder='Enter',
                        type='text',
                        value=''
                    ),
                    ] , style={'width': '10%', 'display': 'inline-block','text-align': 'center'}), 
                    

                ], style={'width': '100%', 'display': 'inline-block'} ),

                html.Div( [
                    html.Div(id='output-container-range-slider')
                ], style={'width': '100%', 'display': 'inline-block'} ),

                  
                html.Div( [  
                    html.Div( [
                        # The graph. 
                        dcc.Graph(
                            id='live-update-image',
                            animate=False,
                            config={
                                'displayModeBar': False
                            }
                        ),
                    ] , style={'width': '40%', 'display': 'inline-block','text-align': 'center'}), 
                    
                    html.Div( [
                        dcc.Graph(
                            id='live-update-histogram',
                            animate=False,
                            config={
                                'displayModeBar': False
                            }
                        ),
                    ] , style={'width': '60%', 'display': 'inline-block','text-align': 'center'}), 
                    
                dcc.Interval(
                    id='interval-component',
                    interval=PLOT_REFRESH_INTERVAL
                ),

                ], style={'width': '100%', 'display': 'inline-block'} ),

                html.Ul(id="afilelist"),
                html.Ul(id="astepfile"),
                html.Ul(id="astepback"),
                html.Ul(id="arunfile"),
                html.Ul(id="aresetfilem"),
                html.Ul(id="abaseline"),
                html.Ul(id="aautoscale"),
                html.Ul(id="a"),
                html.Ul(id="ab"),
            ] )      

        @self.app.callback( 
            dash.dependencies.Output('savebuttonim', 'children'),
            [dash.dependencies.Input('savebuttonim', 'n_clicks')])
        def callback_dropdown(n_clicks):
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
            dash.dependencies.Output(component_id='connectbuttonim', component_property='children'),
            [dash.dependencies.Input(component_id='connectbuttonim', component_property='n_clicks'),
            dash.dependencies.Input(component_id='name-dropdownim', component_property='value')]
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
                    dash.dependencies.Output("afilelist", "children"),
                    [dash.dependencies.Input("readfromfile", "filename")], )
        def readfile_output(filename):
            if filename is not None:
                print (filename)
                filename = '/Users/jeanrintoul/Desktop/mindseyebiomedical/EIT/EIT_Altium/EIT_32/python/EIT_Dashboard/good.bin'
                self.load_file(filename)
                return 'file loaded'
            else: 
                return 'no file'


        @self.app.callback(
                    dash.dependencies.Output("astepfile", "children"),
                    [dash.dependencies.Input("stepfile", "n_clicks")], )
        def step_call(n_clicks):
            if n_clicks is not None:
                print ('step forward')
                self.controller.step_file
                self.process_data()

                return 'step'
            else: 
                return 'not step'

        @self.app.callback(
                    dash.dependencies.Output("astepback", "children"),
                    [dash.dependencies.Input("stepback", "n_clicks")], )
        def stepback_call(n_clicks):
            if n_clicks is not None:
                print ('step back')
                self.controller.step_file_back
                self.process_data()
                return 'step back'
            else: 
                return 'not step back'

        @self.app.callback(
                    dash.dependencies.Output("arunfile", "children"),
                    [dash.dependencies.Input("runfile", "n_clicks")], )
        def runfile(n_clicks):
            if n_clicks is not None:
                self.run_file()
                return 'runfile'
            else: 
                return 'not runfile'

        @self.app.callback(
                    dash.dependencies.Output("aresetfilem", "children"),
                    [dash.dependencies.Input("resetfilem", "n_clicks")], )
        def resetfilemarker(n_clicks):
            if n_clicks is not None:
                self.controller.reset_file()  
                return 'reset filem'
            else: 
                return 'reset not'   

        @self.app.callback(
                    dash.dependencies.Output("abaseline", "children"),
                    [dash.dependencies.Input("baseline", "n_clicks")], )
        def baseline_data(n_clicks):
            if n_clicks is not None:
                self.set_baseline()
                return 'baseline'
            else: 
                return 'not baseline'

        @self.app.callback(
                    dash.dependencies.Output("aautoscale", "children"),
                    [dash.dependencies.Input("autoscale", "n_clicks")], )
        def autoscale_data(n_clicks):
            if n_clicks is not None:
                self.autoscale()  
                return 'autoscale'
            else: 
                return 'not autoscale'            

        @self.app.callback(
                    dash.dependencies.Output("a", "children"),
                    [dash.dependencies.Input("maximum_range", "value")], )
        def change_maxrange(value):
            print (value)
            print (type(value))
            self.rsvaluemin = float(value)
            return 'a'

        @self.app.callback(
                    dash.dependencies.Output("ab", "children"),
                    [dash.dependencies.Input("minimum_range", "value")], )
        def change_minrange(value):
            print (value)
            self.rsvaluemax = float(value)
            return 'ab'
## 
        @self.app.callback(
            dash.dependencies.Output('output-container-range-slider', 'children'),
            [dash.dependencies.Input('range-slider', 'value')])
        def update_output(value):
            print(type(value[0]),value[1])
            # based on value, updated colorbar vmin and vmax. 
            self.vmin = value[0]
            self.vmax = value[1]
            return 'You have selected "{}"'.format(value)
##########

        @self.app.callback(
            Output('container', 'children'),
            [Input('minimum_range', 'value'),
             Input('maximum_range', 'value')])
        def display_controls(datasource_1_value, datasource_2_value):
            v = [datasource_1_value, datasource_2_value]
            # generate 2 dynamic controls based off of the datasource selections
            return html.Div([
                dcc.RangeSlider(
                                id='range-slider',
                                count=1,
                                min=self.range_min,
                                max=self.range_max,
                                step=self.range_step,
                                value=[self.rsvaluemin, self.rsvaluemax]
                            ),
            ])


        @self.app.callback(
            Output('live-update-image', 'figure'),
            events=[Event('interval-component', 'interval')])
        def update_graph_scatter():
            # update the data queue. 
            # if there is data on the queue, do an update. 
            self.process_data()

            if self.algorithm  == 'greit':
                # self.gx,self.gy,self.ds = self.controller.greit_params()
                # self.img = self.ds # numpy.zeros((32,32),dtype=float)
                # If algorithm is GREIT 
                layout = go.Layout(
                    width = 400,
                    height = 400,
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
                #self.gx,self.gy,self.ds = self.controller.greit_params()
                #self.img = self.ds # numpy.zeros((32,32),dtype=float)
                #self.img = numpy.zeros(self.x.shape[0]) 
 
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

                self.img[0] = 5 
                data = FF.create_trisurf(x=self.x, y=self.y, z=self.img,
                                         simplices=self.tri,
                                         color_func=self.dist_origin, # this is equivalent to the mask in tripcolor. 
                                         colormap='Portland',
                                         show_colorbar=False,
                                         title="mesh",
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
            # update the data queue. 
            # self.process_data()
            # this is just dummy data filling in here for now, later it should be the updated img data. 
            # 
            #self.gx,self.gy,self.ds = self.controller.greit_params()
            #self.img = self.ds # numpy.zeros((32,32),dtype=float)

            #self.x,self.y,self.tri,self.el_pos = self.controller.plot_params()
            #self.img = numpy.zeros(self.x.shape[0]) 

            nanless = self.img[~numpy.isnan(self.img)]
            flatimg = (nanless).flatten()
            # print (flatimg)

            data = [go.Histogram(x=flatimg)]

            layout = go.Layout(
                title='Histogram',
                width=700,
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

        return self.layout


