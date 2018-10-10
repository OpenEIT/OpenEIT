import dash

EXTERNAL_CSS = [
    'https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css',
]

EXTERNAL_SCRIPTS = [
]

app = dash.Dash(__name__)

for css in EXTERNAL_CSS:
    app.css.append_css({"external_url": css})

for script in EXTERNAL_SCRIPTS:
    app.scripts.append_script({"external_url": script})

server = app.server
app.config.suppress_callback_exceptions = True
