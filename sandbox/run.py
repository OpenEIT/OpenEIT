import argparse

from data_source import DataSource
from plot import run_plot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i', '--input',
        type=str,
        default=None,
        help='Path to the input file. '
             'If provided, the data will be replayed '
             'from this file instead of being acquired from the board. '
             'Ex: --input "data/output-2018-08-22.csv"'
    )
    parser.add_argument(
        '-f', '--filter',
        action='count',
        default=False,
        help='Whether to filter the input data.'
    )
    parser.add_argument(
        '-s', '--save',
        action='count',
        default=False,
        help='Whether to save the data to a CSV file. '
             'The CSV file will be saved to data/ and its '
             'name will be timestamped.'
    )
    parser.add_argument(
        '-b', '--buffer',
        type=int,
        default=500,
        help='Size of the data history to display in the charts. This is also '
             'the window of points used for PSD computation.'
    )

    args = parser.parse_args()
    source = DataSource(
        input_file=args.input,
        filter_data=args.filter,
        to_csv=args.save
    )
    source.start()

    try:
        run_plot(source)
    except KeyboardInterrupt:
        source.stop()


if __name__ == '__main__':
    main()
