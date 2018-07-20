import dash
from dash.dependencies import Output, Event
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

S_TO_MS = 1000
PLOT_REFRESH_INTERVAL = 0.1 * S_TO_MS


def plot(data_source):
    app = dash.Dash(__name__)
    app.layout = html.Div(
        html.Div([
            dcc.Graph(id='live-update-graph-scatter', animate=False),
            dcc.Interval(
                id='interval-component',
                interval=PLOT_REFRESH_INTERVAL
            )
        ])
    )

    @app.callback(Output('live-update-graph-scatter', 'figure'),
                  events=[Event('interval-component', 'interval')])
    def update_graph_scatter():
        trace1 = go.Scatter(
            x=data_source.x,
            y=data_source.y,
            mode='lines',
            name='Data',
            # line={'shape': 'spline'}
        )

        trace2 = go.Scatter(
            x=data_source.x,
            y=data_source.y_filtered,
            mode='lines',
            name='Filtered data',
            # line={'shape': 'spline'}
        )

        data = [trace1, trace2]

        x_min = min(data_source.x)
        x_max = max(data_source.x)
        y_min = min(data_source.y)
        y_max = max(data_source.y)

        layout = go.Layout(
            xaxis={'range': [x_min, x_max]},
            yaxis={'range': [y_min, y_max]}
        )

        return {'data': data, 'layout': layout}

    app.run_server()
