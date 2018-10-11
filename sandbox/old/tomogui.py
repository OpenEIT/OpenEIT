import logging
import os
import dash
from dash.dependencies import Output, Event
import dash_core_components as dcc
import dash_html_components as html
import plotly.plotly as py
import plotly.graph_objs as go
import matplotlib.cm as cm
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

class Tomogui(object):

    def __init__(self, controller):

        self.controller = controller
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

    # Get's new data off the serial port. 
    def process_data(self):
        while not self.controller.data_queue.empty():
            f,amp = self.controller.data_queue.get()
            self.data_dict[f] = amp

        self.freqs = list(self.data_dict.keys())
        self.psd   = list(self.data_dict.values())


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

    def plotly_trisurf(self,x, y, z, simplices, colormap=cm.RdBu, plot_edges=None):
        #x, y, z are lists of coordinates of the triangle vertices 
        #simplices are the simplices that define the triangularization;
        #simplices  is a numpy array of shape (no_triangles, 3)
        #insert here the  type check for input data

        points3D=np.vstack((x,y,z)).T
        tri_vertices=map(lambda index: points3D[index], simplices)# vertices of the surface triangles     
        zmean=[np.mean(tri[:,2]) for tri in tri_vertices ]# mean values of z-coordinates of 
                                                          #triangle vertices
        min_zmean=np.min(zmean)
        max_zmean=np.max(zmean)
        facecolor=[map_z2color(zz,  colormap, min_zmean, max_zmean) for zz in zmean]
        I,J,K=tri_indices(simplices)

        triangles=go.Mesh3d(x=x,
                         y=y,
                         z=z,
                         facecolor=facecolor,
                         i=I,
                         j=J,
                         k=K,
                         name=''
                        )

        if plot_edges is None:# the triangle sides are not plotted 
            return [triangles]
        else:
            #define the lists Xe, Ye, Ze, of x, y, resp z coordinates of edge end points for each triangle
            #None separates data corresponding to two consecutive triangles
            lists_coord=[[[T[k%3][c] for k in range(4)]+[ None]   for T in tri_vertices]  for c in range(3)]
            Xe, Ye, Ze=[reduce(lambda x,y: x+y, lists_coord[k]) for k in range(3)]

            #define the lines to be plotted
            lines=go.Scatter3d(x=Xe,
                            y=Ye,
                            z=Ze,
                            mode='lines',
                            line=dict(color= 'rgb(50,50,50)', width=1.5)
                   )
            return [triangles, lines]

    def run(self):

        app = dash.Dash()
        app.css.config.serve_locally = True
        app.scripts.config.serve_locally = True
        app.layout = html.Div( [

                html.Link(
                    rel='stylesheet',
                    href='/static/stylesheet.css'
                ),


                html.Div( [

                    html.Div( [
                        html.P('Realtime Control: '),
                    ], style={'width': '10%', 'display': 'inline-block','text-align': 'center'} ),
                    

                    html.Div( [
                    # the button controls      
                    dcc.Dropdown(
                        id='name-dropdown',
                        options=[{'label':name, 'value':name} for name in self.portnames],
                        placeholder = 'Select Port',
                        value = self.portnames[0]
                        ),
                    ], style={'width': '30%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    html.Button(children='Connect', id='connectbutton', type='submit'),
                    ], style={'width': '10%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    html.Button(children='Save Current Spectrum', id='savebutton', type='submit'),
                    ] , style={'width': '10%', 'display': 'inline-block','text-align': 'center'}),

                    html.Div( [
                    html.Button(children='Baseline', id='baseline', type='submit'),
                    ] , style={'width': '10%', 'display': 'inline-block','text-align': 'center'}),

                    html.Div( [
                    html.Button(children='Autoscale', id='autoscale', type='submit'),
                    ] , style={'width': '15%', 'display': 'inline-block','text-align': 'center'}),

                    html.Div( [
                    html.Button(children='Update Histogram', id='histogram', type='submit'),
                    ] , style={'width': '15%', 'display': 'inline-block','text-align': 'center'}),

                ], style={'width': '100%', 'display': 'inline-block'} ),

                html.Div( [
                                        # the button controls      
                    html.Div( [
                    html.P('Offline File Control: '),
                    ], style={'width': '15%', 'display': 'inline-block','text-align': 'center'} ),

                    # the button controls      
                    html.Div( [
                    html.Button(children='Read from File', id='readfromfile', type='submit'),
                    ], style={'width': '15%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    html.Button(children='Step', id='stepfile', type='submit'),
                    ], style={'width': '10%', 'display': 'inline-block','text-align': 'center'} ),

                    html.Div( [
                    html.Button(children='Step Back', id='stepbackfile', type='submit'),
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

                    html.Div( [
                        dcc.RangeSlider(
                            id='range-slider',
                            count=1,
                            min=-5,
                            max=10,
                            step=0.5,
                            value=[-3, 7]
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

                  
                # The graph. 
                dcc.Graph(
                    id='live-update-image',
                    animate=False,
                    config={
                        'displayModeBar': False
                    }
                ),
                dcc.Graph(
                    id='live-update-histogram',
                    animate=False,
                    config={
                        'displayModeBar': False
                    }
                ),
                dcc.Interval(
                    id='interval-component',
                    interval=PLOT_REFRESH_INTERVAL
                ),

            
            ] )      

        @app.server.route('/static/<path:path>')
        def static_file(path):
            static_folder = os.path.join(os.getcwd(), 'static')
            return send_from_directory(static_folder, path)

        @app.callback( 
            dash.dependencies.Output('savebutton', 'children'),
            [dash.dependencies.Input('savebutton', 'n_clicks')])
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


        @app.callback(
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
     
        @app.callback(
            dash.dependencies.Output('output-container-range-slider', 'children'),
            [dash.dependencies.Input('range-slider', 'value')])
        def update_output(value):
            return 'You have selected "{}"'.format(value)

        @app.callback(
            Output('live-update-image', 'figure'),
            events=[Event('interval-component', 'interval')])
        def update_graph_scatter():
            # update the data queue. 
            #self.process_data()

            data3=plotly_trisurf(x,y,z, faces, colormap=cm.RdBu, plot_edges=None)

            title="Trisurf from a PLY file<br>"+\
                            "Data Source:<a href='http://people.sc.fsu.edu/~jburkardt/data/ply/airplane.ply'> [1]</a>"

            noaxis=dict(showbackground=False,
                        showline=False,
                        zeroline=False,
                        showgrid=False,
                        showticklabels=False,
                        title=''
                      )

            fig3 = go.Figure(data=data3, layout=layout)
            fig3['layout'].update(dict(title=title,
                                       width=1000,
                                       height=1000,
                                       scene=dict(xaxis=noaxis,
                                                  yaxis=noaxis,
                                                  zaxis=noaxis,
                                                  aspectratio=dict(x=1, y=1, z=0.4),
                                                  camera=dict(eye=dict(x=1.25, y=1.25, z= 1.25)
                                                 )
                                       )
                                 ))

            py.iplot(fig3, filename='Chopper-Ply-cls')

            # if len(self.data_dict.keys()) > 0:
            #     trace1 = go.Scatter(
            #         x=list(self.data_dict.keys()),
            #         y=list(self.data_dict.values()),
            #         mode='lines',
            #         name='PSD',
            #         line={'shape': 'spline'},
            #         fill='tozeroy'
            #     )

            #     data = [trace1]

            #     layout = go.Layout(
            #         title='Bioimpedance Spectroscopy',
            #         xaxis=dict(
            #             title='Frequency (Hz)',
            #             type='linear',
            #             autorange=True
            #         ),
            #         yaxis=dict(
            #             title='Amplitude',
            #             autorange=True
            #         )
            #     )

            return {'data': data, 'layout': layout}

        # @app.callback(
        #     Output('live-update-spectrogram', 'figure'),
        #     events=[Event('interval-component', 'interval')])
        # def update_graph_scatter():
        #     # update the data queue. 
        #     self.process_data()

        #     if len(self.data_dict.keys()) > 0:
        #         trace1 = go.Scatter(
        #             x=list(self.data_dict.keys()),
        #             y=list(self.data_dict.values()),
        #             mode='lines',
        #             name='PSD',
        #             line={'shape': 'spline'},
        #             fill='tozeroy'
        #         )

        #         data = [trace1]

        #         layout = go.Layout(
        #             title='Bioimpedance Spectroscopy',
        #             xaxis=dict(
        #                 title='Frequency (Hz)',
        #                 type='linear',
        #                 autorange=True
        #             ),
        #             yaxis=dict(
        #                 title='Amplitude',
        #                 autorange=True
        #             )
        #         )

        #         return {'data': data, 'layout': layout}
        #         
        # _LOGGER.debug('App running at: http://localhost:%s' % PORT)
        app.run_server(port=PORT)


    # def quit(self):
    #     self.root.quit()     # stops mainloop
    #     self.root.destroy()  # this is necessary on Windows to prevent
    #     # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    #     sys.exit()
