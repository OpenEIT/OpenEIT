from . import time_series
from . import spectroscopy
from . import imaging


class Mode(object):
    def __init__(self, name, layout=None):
        self.name = name
        self.layout = layout
        self.id = name # slugify(self.name)
        self.url = '/{}'.format(self.id)

mode_names = [
    Mode(name='TimeSeries', layout=time_series.layout),
    Mode(name='Spectroscopy', layout=spectroscopy.layout),
    Mode(name='Imaging', layout=imaging.layout),
]
