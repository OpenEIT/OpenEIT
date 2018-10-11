from .controller import Controller
# from .singlefrequencygui import Singlefrequencygui
# from .meshgui import Meshgui
# from .multifrequencygui import Multifrequencygui
# from .timeseriesgui import Timeseriesgui
# from .bisgui import BISgui
# from .tomogui import Tomogui
# from .app import appConfig
# from .modes import time_series
# from slugify import slugify
from .dash_control import runGui
# from . import app 
# from . import navbar
from . import page_not_found
from .state import State

from .modes import time_series
# from .modes import bioimpedance
from .modes import spectroscopy
from .modes import imaging


# class Mode(object):
#     def __init__(self, name, layout=None):
#         self.name = name
#         self.layout = layout
#         self.id = name # slugify(self.name)
#         self.url = '/{}'.format(self.id)

# modes = [
#     Mode(name='Time Series', layout=time_series.layout),
#     Mode(name='Bioimpedance', layout=bioimpedance.layout),
#     Mode(name='Spectroscopy', layout=spectroscopy.layout),
#     Mode(name='Imaging', layout=imaging.layout),
# ]
