import logging
import queue
import os

import openeit.reconstruction
import openeit.backend


logger = logging.getLogger(__name__)


class PlaybackStrategy:

    def rewind(self):
        raise NotImplementedError

    def step(self):
        raise NotImplementedError

    def step_back(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError


class FilePlayback(PlaybackStrategy):
    """
    This playback strategy allows to directly feed data from files to
    the reconstruction process.
    """

    def __init__(self, file_handle, controller):
        res = []
        for line in file_handle:
            data = openeit.backend.parse_line(line)
            if data is not None:
                res.append(data)

        self._file_data = res
        self._file_marker = 0
        self._queue = controller._data_queue

    def close(self):
        pass

    def rewind(self):
        self._file_marker = 0

    def step(self):
        if self._file_marker < len(self._file_data):
            self._queue.put(self._file_data[self._file_marker])
            self._file_marker += 1
            return True
        return False

    def step_back(self):
        if self._file_marker > 0:
            self._file_marker -= 1
            self._queue.put(self._file_data[self._file_marker])
            return True
        return False


class VirtualSerialPortPlayback(PlaybackStrategy):
    """
    This playback strategy is used for testing the serial-port
    handling without needing the hardware. It sets up a PTY and
    connects the serial handler to the slave end of the PTY.

    .. note:: This only works on POSIX systems (which support PTYs).
    """

    def __init__(self, file_handle, controller):
        self._data_file_array = file_handle.readlines()
        self._file_marker = 0
        self._master_fd, self._slave_fd = os.openpty()
        controller.serial_handler.connect(os.ttyname(self._slave_fd))
        self._pty_master = os.fdopen(self._master_fd, "w")

    def close(self):
        os.close(self._slave_fd)
        self._pty_master.close()

    def rewind(self):
        self._file_marker = 0

    def step(self):
        if self._file_marker < len(self._data_file_array):
            self._pty_master.write(self._data_file_array[self._file_marker])
            self._file_marker += 1
            return True
        return False

    def step_back(self):
        if self._file_marker > 0:
            self._file_marker -= 1
            self._pty_master.write(self._data_file_array[self._file_marker])
            return True
        return False


class Controller:

    def __init__(self):
        self._signal_connections = {}

        self.recording = False

        # setup the queues for the workers
        self._data_queue = queue.Queue()
        self._image_queue = queue.Queue()

        # intialize the reconstruction worker
        self.image_pixels = 100
        self.image_reconstruct = openeit.reconstruction.ReconstructionWorker(
            self.image_pixels,
            self._data_queue,
            self._image_queue
        )
        self.image_reconstruct.start()

        # instanciate the serial handler
        self.serial_handler = openeit.backend.SerialHandler(self._data_queue)

        self.playback = None

    def configure(self, *, initial_port=None, virtual_tty=False,
                 read_file=False):
        if initial_port is not None:
            if virtual_tty:
                with open(initial_port, "r") as file_handle:
                    self.playback = VirtualSerialPortPlayback(file_handle,
                                                              self)
                    self.emit("connection_state_changed", True)
            elif read_file:
                with open(initial_port, "r") as file_handle:
                    self.playback = FilePlayback(file_handle, self)
                    self.emit("connection_state_changed", True)
            else:
                self.menuselect.set(initial_port)
                self.connect()

    @property
    def image_queue(self):
        return self._image_queue

    def register(self, signal, callable_):
        # TODO: supply a cookie for disconnecting
        self._signal_connections.setdefault(signal, []).append(callable_)

    def emit(self, signal, *args, **kwargs):
        for handler in self._signal_connections.get(signal, ()):
            handler(*args, **kwargs)

    def connect(self, port):
        self.serial_handler.connect(port)
        self.emit("connection_state_changed", True)

    def disconnect(self):
        if self.playback is not None:
            self.playback.close()
            self.playback = None

        self.serial_handler.disconnect()
        self.emit("connection_state_changed", False)

    def load_file(self, file_handle):
        self.disconnect()
        self.playback = FilePlayback(file_handle, self)
        self.emit("connection_state_changed", True)

    def step_file(self):
        if self.playback is not None:
            return self.playback.step()
        return False

    def step_file_back(self):
        if self.playback is not None:
            return self.playback.step_back()
        return False

    def run_file(self):
        if self.playback is not None:
            if self.playback.step():
                self.root.after(10, self.run_file)

    def reset_file(self):
        if self.playback is not None:
            self.playback.rewind()

    def start_recording(self):
        if self.serial_handler.recording:
            return

        self.serial_handler.start_recording()
        self.emit("recording_state_changed", True)

    def stop_recording(self):
        if not self.serial_handler.recording:
            return

        self.serial_handler.stop_recording()
        self.emit("recording_state_changed", False)

    def shutdown(self):
        # stop recording to flush the buffers
        self.stop_recording()
