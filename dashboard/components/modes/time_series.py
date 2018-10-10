import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app

# TODO: placeholder layout and callbacks. Replace with your own.

layout = html.Div([
    html.H5('Example content. Replace with the proper mode visualization.'),
    dcc.Dropdown(
        id='time-series-dropdown',
        options=[
            {'label': item, 'value': item} for item in ['Example 1', 'Example 2']
        ]
    ),
    html.Div(id='time-series-display-value'),
])


@app.callback(
    Output('time-series-display-value', 'children'),
    [Input('time-series-dropdown', 'value')])
def display_value(value):
    return 'You have selected "{}"'.format(value)
