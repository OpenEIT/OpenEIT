import logging
import os

import dash
from dash.dependencies import Output, Event
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

PORT = 8050
S_TO_MS = 1000
PLOT_REFRESH_INTERVAL = 0.1 * S_TO_MS

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)
_LOGGER.addHandler(logging.StreamHandler())

# Suppress unnecessary debug / warning messages from Flask
os.environ['FLASK_ENV'] = 'development'
flask_logger = logging.getLogger('werkzeug')
flask_logger.setLevel(logging.INFO)


def run_plot(data_source):
    app = dash.Dash(__name__)
    app.layout = html.Div(
        children=[
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
                interval=PLOT_REFRESH_INTERVAL
            )
        ])

    @app.callback(Output('live-update-time-series', 'figure'),
                  events=[Event('interval-component', 'interval')])
    def update_graph_scatter():
        if len(data_source.x) > 0:
            trace1 = go.Scatter(
                x=data_source.x,
                y=data_source.y,
                mode='lines',
                name='Data',
                # line={'shape': 'spline'}
            )

            data = [trace1]

            if len(data_source.y_filtered) > 0:
                trace2 = go.Scatter(
                    x=data_source.x,
                    y=data_source.y_filtered,
                    mode='lines',
                    name='Filtered Data',
                    # line={'shape': 'spline'}
                )
                data.append(trace2)


            x_min = min(data_source.x)
            x_max = max(data_source.x)
            y_min = min(data_source.y)
            y_max = max(data_source.y)

            layout = go.Layout(
                title='OpenEIT Data',
                xaxis=dict(
                    title='Time',
                    range=[x_min, x_max]
                ),
                yaxis=dict(
                    title='Impedance (ohms)',
                    range=[y_min, y_max]
                )
            )

            return {'data': data, 'layout': layout}

    @app.callback(Output('live-update-psd', 'figure'),
                  events=[Event('interval-component', 'interval')])
    def update_graph_scatter():
        if len(data_source.x) > 0:
            trace1 = go.Scatter(
                x=data_source.freqs,
                y=data_source.psd,
                mode='lines',
                name='PSD',
                line={'shape': 'spline'},
                fill='tozeroy'
            )

            data = [trace1]

            layout = go.Layout(
                title='Power Spectrum Density',
                xaxis=dict(
                    title='Frequency (Hz)',
                    type='log',
                    autorange=True
                ),
                yaxis=dict(
                    title='Power (dB)',
                    autorange=True
                )
            )

            return {'data': data, 'layout': layout}

    _LOGGER.debug('App running at: http://localhost:%s' % PORT)
    app.run_server(port=PORT)
