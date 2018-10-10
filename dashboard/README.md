OpenEIT Dashboard
-----------------

Visualization dashboard for OpenEIT.

## Requirements
```
Python 3.6.1+
```

## Install
```
pip -r requirements.txt
```

## Run
```
python run.py
```

## How to add more visualizations
> Note: Visualization types are called `modes`. Each mode visualization lives in `dashboard/components/modes`.

To add your own mode visualization:
* Create a new file in `dashboard/components/modes`, for example `my_mode.py`.
* Create a new [`Dash layout`](https://dash.plot.ly/getting-started). Example:
```python
# dashboard/components/modes/my_mode.py

import dash_html_components as html

layout = html.Div([html.H3('Hello, world!')])
```
* Edit `dashboard/components/modes/__init__.py` and add information about the new mode. Example:
```python
# dashboard/components/modes/__init__.py

...
from components.modes import my_mode

modes = [
    Mode(name='Time Series', layout=time_series.layout),
    Mode(name='Bioimpedance', layout=bioimpedance.layout),
    Mode(name='Spectroscopy', layout=spectroscopy.layout),
    Mode(name='Imaging', layout=imaging.layout),

    # Add your new mode info here
    Mode(name='My Mode', layout=my_mode.layout)
]
```
* That's it! Run the app and your new mode viz should appear in the dashboard, under its own navigation tab.

> Note: If you new mode requires some special settings for the board, we recommend that you add this logic in the `state.State` class, inside the `set_mode()` method.
