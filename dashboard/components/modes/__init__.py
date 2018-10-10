from slugify import slugify
from components.modes import time_series
from components.modes import bioimpedance
from components.modes import spectroscopy
from components.modes import imaging


class Mode(object):
    def __init__(self, name, layout=None):
        self.name = name
        self.layout = layout
        self.id = slugify(self.name)
        self.url = '/{}'.format(self.id)


modes = [
    Mode(name='Time Series', layout=time_series.layout),
    Mode(name='Bioimpedance', layout=bioimpedance.layout),
    Mode(name='Spectroscopy', layout=spectroscopy.layout),
    Mode(name='Imaging', layout=imaging.layout),
]
