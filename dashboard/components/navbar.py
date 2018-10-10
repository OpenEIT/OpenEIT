import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from components.modes import modes

logo_url = 'https://s3-us-west-2.amazonaws.com/open-eit/logo-white.png'

navbar_brand = dcc.Link(
    html.Div([
        html.Img(
            src=logo_url,
            style={'height': 30, 'margin-right': 10}),
        'OpenEIT Dashboard'
    ]),
    style={'margin-right': 40},
    className="navbar-brand",
    href='/'
)

layout = html.Div([
    navbar_brand,
    html.Div(id='navbar-links', className='btn-group')
], className='navbar navbar-expand-lg navbar-dark bg-dark')


@app.callback(Output('navbar-links', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    navbar_links = []
    for mode in modes:
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
