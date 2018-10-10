from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc

from app import app
from state import state
from components import navbar, page_not_found
from components.modes import modes

app.layout = html.Div([
    navbar.layout,
    dcc.Location(id='url', refresh=False),
    html.Div([
        html.Div(id='page-content')
    ], id='main-container', style={'margin': 15})
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    layout = page_not_found.layout
    for mode in modes:
        if pathname == mode.url:
            state.set_mode(mode)
            layout = html.Div([html.H3(mode.name), mode.layout])
    return layout


if __name__ == '__main__':
    app.run_server(debug=True)
