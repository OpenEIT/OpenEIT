from open_eit_sandbox.data_source import DataSource
from open_eit_sandbox.line_chart import plot

MOCK = False
FILTER = True

if __name__ == '__main__':

    source = DataSource(mock=MOCK, filter_data=FILTER)
    source.start()

    try:
        plot(source)
    except KeyboardInterrupt:
        source.stop()
