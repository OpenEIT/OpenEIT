


class State(object):
    """
    Holds the app states. For example, the OpenEIT mode currently selected.
    """

    def __init__(self):
        self.mode = None

    def set_mode(self, mode):
        # TODO: this is where custom logic to communicate with the OpenEIT board
        # should live, in the event you need so change some firwmare settings
        # for a specific mode.
        self.mode = mode


# state = State()
