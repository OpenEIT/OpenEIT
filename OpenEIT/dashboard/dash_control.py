"""

# Copyright (c) Mindseye Biomedical LLC. All rights reserved.
# Distributed under the (new) CC BY-NC-SA 4.0 License. See LICENSE.txt for more info.

"""
import dash 
import logging
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
from . import page_not_found
from . import state 
from .modes import mode_names
from .modes import spectroscopy
from .modes import time_series
from .modes import imaging
from .modes import fw
import os 
import urllib

logger = logging.getLogger(__name__)

class runGui(object):

    def __init__(self, controller, debug=False):

        # Both controller and app have to be passed to the dynamically loaded page to enable callbacks and functionality with the rest of the package. 
        self.debug = debug
        self.controller = controller
        self.app = None

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

        self.app = dash.Dash()
        self.app.css.config.serve_locally = True
        self.app.scripts.config.serve_locally = True
        # server = app.server
        self.app.config.suppress_callback_exceptions = True
                        
        # load it all up at the start so new routes aren't made after the server is started.                 
        self.bis_display = spectroscopy.BISgui(self.controller,self.app)
        self.bislayout = self.bis_display.return_layout()

        self.time_series_display = time_series.Timeseriesgui(self.controller,self.app)
        self.time_serieslayout = self.time_series_display.return_layout()        

        self.imaging_display = imaging.Tomogui(self.controller,self.app)
        self.imaginglayout = self.imaging_display.return_layout()   

        self.fw_display = fw.FWgui(self.controller,self.app)
        self.fwlayout = self.fw_display.return_layout()  
        
        logger.info("openeit_server_started")


    def run(self):

        self.app.layout = html.Div([
            # stylesheet. 
            html.Link(
                rel='stylesheet',
                href='/static/bootstrap.min.css'
            ),

            # logo and brand name 
            html.Div([
                dcc.Link(
                html.Div([
                    html.Img(
                        src='static/logo-white.png',
                        style={'height': 30, 'margin-right': 10}),
                    'OpenEIT Dashboard'
                ]),
                style={'margin-right': 40},
                className="navbar-brand",
                href='/'
                ),
                # navbar links
                html.Div(id='navbar-links', className='btn-group'),

                html.Div([
                    html.Pre('    '),
                    html.Button(
                        'Record',
                        id='recordbutton',
                        #type ='submit',
                        className='btn btn-light'),

                ], className='btn-group'),

                html.Div([
                    html.Pre('    '),
                    html.A(children='Download', 
                        id='download-link',
                        download="rawdata.txt",
                        href="",
                        target="_blank"
                    ),
                ], className='btn-group'),
            ], className='navbar navbar-expand-lg navbar-dark bg-dark'), 

            dcc.Location(id='url', refresh=False),

            # this is the page that appears when the buttons are pressed. 
            html.Div([
                html.Div(id='page-content')
            ], id='main-container', style={'margin': 15})

        ])

        # set_mode('')
        s = state.State()
        # the current state is none... which I suppose is ok. 
        #print (s.mode)

        @self.app.server.route('/static/<path:path>')
        def static_file(path):
            static_folder = os.path.join(os.getcwd(), 'static')
            return send_from_directory(static_folder, path)

        @self.app.callback( 
            dash.dependencies.Output('recordbutton', 'children'),
            [dash.dependencies.Input('recordbutton', 'n_clicks')])
        def callback_dropdown(n_clicks):
            if n_clicks is not None:
                if self.recording == False:
                    if self.connected == True: 
                        self.controller.start_recording()
                        return 'Stop Recording'
                    else: 
                        #print ('comms not connected')
                        return 'Record'
                else:
                    print ('stop recording')
                    self.controller.stop_recording()
                    return 'Record'
            else: 
                return 'Record'

        # This displays the page, it should also pass the app and controller info to the class. 
        @self.app.callback(Output('page-content', 'children'),
                      [Input('url', 'pathname')])
        def display_page(pathname):
            layout = html.Div([self.fwlayout]) #page_not_found.layout
            for mode in mode_names:
                if pathname == mode.url:
                    print (mode.name)
                    s.set_mode(mode)
                    # instantiate the particular mode. 
                    if mode.name == 'Spectroscopy': 
                        layout = html.Div([self.bislayout])
                    elif mode.name == 'TimeSeries':
                        layout = html.Div([self.time_serieslayout ])
                    elif mode.name == 'Imaging':
                        layout = html.Div([self.imaginglayout])
                    else:
                        layout = html.Div([self.fwlayout])

            return layout

 
        @self.app.callback(Output('navbar-links', 'children'),
                      [Input('url', 'pathname')])
        def display_nav(pathname):
            navbar_links = []
            modes = mode_names
            for mode in modes:
                # print (mode.name)
                class_name = 'btn btn-outline-light'
                if mode and mode.url == pathname:
                    class_name = 'btn btn-light'
                link = dcc.Link(
                    mode.name,
                    id='{}-button'.format(mode.id),
                    className=class_name,
                    href=mode.url)
                navbar_links.append(link)

            return navbar_links

        @self.app.callback(
            dash.dependencies.Output('download-link', 'href'),
            [dash.dependencies.Input('recordbutton', 'n_clicks')])
        def update_download_link(n_clicks):
            if n_clicks is not None:
                if self.recording == False:
                    return 'hi there'
                    # if self.connected == True: 
                    #     self.controller.start_recording()
                    #     return ''
                    # else: 
                    #     print ('comms not connected')
                    #     return ''
                else:
                    datastream = self.controller.serial_getbytestream()
                    # print (datastream)
                    #csv_string = datastream.to_csv(index=False, encoding='utf-8')
                    csv_string = "data:text/txt;charset=utf-8," + urllib.parse.quote(datastream)
                    return csv_string  
  
        # Switch to False    
        self.app.run(debug=self.debug)

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
