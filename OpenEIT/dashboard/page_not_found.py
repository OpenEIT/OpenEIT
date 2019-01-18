"""

# Copyright (c) Mindseye Biomedical LLC. All rights reserved.
# Distributed under the (new) CC BY-NC-SA 4.0 License. See LICENSE.txt for more info.

"""
import dash_core_components as dcc
import dash_html_components as html

from .modes.modes import mode_names

modes = mode_names

# layout = html.Div([html.H5('Hello, world!')])

parent_div = [html.H3('Page Not Found')]
for mode in modes:
    div = html.Div(dcc.Link('Go to {}'.format(mode.name), href=mode.url))
    parent_div.append(div)

layout = html.Div(parent_div)
