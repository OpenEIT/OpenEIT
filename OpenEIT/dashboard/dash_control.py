import time
"""

# Copyright (c) Mindseye Biomedical LLC. All rights reserved.
# Distributed under the (new) CC BY-NC-SA 4.0 License. See LICENSE.txt for more info.

"""
import dash 
import logging
from dash.dependencies import Input, Output
from dash import html
from dash import dcc
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
                    html.Span(id='record-status', style={'color': 'white'}),
                ], className='btn-group'),
                dcc.Download(id='download-raw'),
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
            [Output('recordbutton', 'children'),
             Output('record-status', 'children'),
             Output('download-raw', 'data')],
            [Input('recordbutton', 'n_clicks')],
            prevent_initial_call=True)
        def toggle_recording(n_clicks):
            # Single callback: start on first click, stop + download on the next.
            if not self.controller.serial_handler.recording:
                if not self.connected:
                    return 'Record', 'connect first', dash.no_update
                self.controller.start_recording()
                return 'Stop Recording', 'recording...', dash.no_update
            self.controller.stop_recording()
            datastream = self.controller.serial_getbytestream()
            if not datastream:
                return 'Record', 'no data received', dash.no_update
            fname = time.strftime('rawdata_%Y%m%d_%H%M%S.txt')
            nlines = datastream.count('\n')
            return 'Record', 'saved {} lines'.format(nlines), dcc.send_string(datastream, fname)

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
