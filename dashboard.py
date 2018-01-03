
import argparse
import logging
import os
import queue
import sys
import time
import tkinter

import OpenEIT.reconstruction
import OpenEIT.backend

import serial.tools.list_ports

import numpy

import matplotlib
import matplotlib.pyplot as mpl
matplotlib.use("TkAgg")
# mpl.use('Qt4Agg')


# TODO: Separate Control and View!
# a first step in this direction has been done with the playback
# strategies.

# TODO: Improve State Feedback
# The current connection and playback state should be clearly visible
# at all times


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

    def __init__(self, file_handle, gui):
        res = []
        for line in file_handle:
            data = OpenEIT.backend.parse_line(line)
            if data is not None:
                res.append(data)

        self._file_data = res
        self._file_marker = 0
        self._queue = gui._data_queue

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

    def __init__(self, file_handle, gui):
        self._data_file_array = file_handle.readlines()
        self._file_marker = 0
        self._master_fd, self._slave_fd = os.openpty()
        gui.s.connect(os.ttyname(self._slave_fd))
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


class Gui(object):

    def __init__(self, *, initial_port=None, virtual_tty=False,
                 read_file=False):

        self.root = tkinter.Tk()
        self.root.wm_title("EIT Test Bench Dashboard")
        self.top = None
        self.topplot = None
        self.topcanvas = None
        self.topcbar = None
        self.topcbaxes = None

        self.recording = False

        menu = tkinter.Menu(self.root)
        self.root.config(menu=menu)

        filemenu = tkinter.Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Exit", command=self.root.quit)
        viewmenu = tkinter.Menu(menu)
        menu.add_cascade(label="View", menu=viewmenu)
        viewmenu.add_command(label="Dedicated Reconstruction Window",
                             command=self.Eitwin)
        viewmenu.add_separator()
        viewmenu.add_command(label="something else",
                             command=self.Something_else)
        helpmenu = tkinter.Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About...",
                             command=self.About)

        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        # make Esc exit the program
        self.root.bind('<Escape>', lambda e: self.root.destroy())

        # Matplotlibbing.
        fig = mpl.Figure(figsize=(5, 4), dpi=100)
        # pos = [left, bottom, width, height]
        image_position = [0.1, 0.25, 0.7, 0.7]
        histogram_position = [0.1, 0.08, 0.8, 0.1]
        colorbar_position = [0.85, 0.25, 0.03, 0.7]
        self.imageplt = fig.add_axes(image_position)
        self.histplt = fig.add_axes(histogram_position)
        self.cbaxes = fig.add_axes(colorbar_position)

        # 180,225,270,315,0,45,90,135
        # 1,2,3,4,5,6,7,8
        # Add text for electrode locations.
        self.imageplt.annotate('180d(AFE1)',
                               xy=(0.4, 0.9),
                               xycoords='axes fraction')
        self.imageplt.annotate('225d(AFE2)',
                               xy=(0.15, 0.75),
                               xycoords='axes fraction')
        self.imageplt.annotate('270d(AFE3)',
                               xy=(0.0, 0.5),
                               xycoords='axes fraction')
        self.imageplt.annotate('315d(AFE4)',
                               xy=(0.2, 0.2),
                               xycoords='axes fraction')
        self.imageplt.annotate('0d(AFE5)',
                               xy=(0.5, 0.1),
                               xycoords='axes fraction')
        self.imageplt.annotate('45d(AFE6)',
                               xy=(0.75, 0.25),
                               xycoords='axes fraction')
        self.imageplt.annotate('90d(AFE7)',
                               xy=(0.9, 0.5),
                               xycoords='axes fraction')
        self.imageplt.annotate('135d(AFE8)',
                               xy=(0.8, 0.8),
                               xycoords='axes fraction')

        ypadding = 10

        # Will this often need to be changed?
        scale_max = 90000
        self.sliders = [-100, scale_max, -100, scale_max]

        min_cbar = 0
        max_cbar = scale_max
        scale_tick_interval = float(scale_max/10)

        # setup the queues for the workers
        self._data_queue = queue.Queue()
        self._image_queue = queue.Queue()

        # intialize the reconstruction worker
        self.image_pixels = 100
        self.image_reconstruct = OpenEIT.reconstruction.ReconstructionWorker(
            self.image_pixels,
            self._data_queue,
            self._image_queue
        )
        self.image_reconstruct.start()

        self._baseline = numpy.zeros((self.image_pixels, self.image_pixels),
                                     dtype=numpy.float)
        self.img = self._baseline

        self.plot = self.imageplt.imshow(self.img, interpolation='nearest')

        # self.imageplt.set_position(image_position) # set a new position
        # self.histplt.set_position(histogram_position)
        self.cbar = mpl.colorbar(self.plot, cax=self.cbaxes)
        # self.cbar = mpl.pyplot.colorbar(self.imageplt,cax = self.cbaxes)
        self.cbar.set_clim([min_cbar, max_cbar])
        #
        self.canvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(
            fig,
            master=self.root
        )

        self.canvas.show()
        self.canvas.get_tk_widget().pack(side=tkinter.TOP,
                                         fill=tkinter.BOTH,
                                         expand=1)
        toolbar = matplotlib.backends.backend_tkagg.NavigationToolbar2TkAgg(
            self.canvas,
            self.root
        )
        toolbar.update()
        self.canvas._tkcanvas.pack(side=tkinter.TOP,
                                   fill=tkinter.BOTH,
                                   expand=1)
        # canvas.mpl_connect('key_press_event', on_key_event)
        self.total_rendering_time = 0.0
        self.total_processing_time = 0.0

        # ---------------
        # defining frames
        # ---------------
        bottomframe0 = tkinter.Frame(self.root)
        bottomframe1 = tkinter.Frame(self.root)
        bottomframe2 = tkinter.Frame(self.root)
        bottomframe3 = tkinter.Frame(self.root)

        bottomframe0.pack(side=tkinter.TOP)
        bottomframe1.pack(side=tkinter.TOP)
        bottomframe2.pack(side=tkinter.TOP)
        bottomframe3.pack(side=tkinter.TOP)

        # This is the text box...
        self._text = tkinter.StringVar()
        self.msg = tkinter.Label(
            bottomframe0,
            bg="light cyan", textvariable=self._text
        )
        self.msg.pack(fill="x", expand=True)

        # sliders.
        self.w1 = tkinter.Scale(bottomframe0, from_=self.sliders[0],
                                to=self.sliders[1], length=600,
                                tickinterval=scale_tick_interval,
                                orient=tkinter.HORIZONTAL,
                                label='MIN')
        self.w1.set(scale_max/10)
        self.w1.pack(fill="x", expand=True)
        self.w2 = tkinter.Scale(bottomframe0, from_=self.sliders[2],
                                to=self.sliders[3], length=600,
                                tickinterval=scale_tick_interval,
                                orient=tkinter.HORIZONTAL,
                                label='MAX')
        self.w2.set(9*scale_max/10)
        self.w2.pack(fill="x", expand=True)

        # Text entry boxes for min and max range of each slider bar.
        cbarbut = tkinter.Button(bottomframe0, text='Update HIST',
                                 command=self.update_hist)
        cbarbut.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

        cbarbut = tkinter.Button(bottomframe0, text='Update CBAR',
                                 command=self.update_cbar)
        cbarbut.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

        self.hist_update = False

        self.min_slider_l = tkinter.Entry(bottomframe0)
        self.min_slider_h = tkinter.Entry(bottomframe0)
        self.max_slider_l = tkinter.Entry(bottomframe0)
        self.max_slider_h = tkinter.Entry(bottomframe0)
        self.max_slider_h.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)
        self.max_slider_h_label = tkinter.Label(bottomframe0, text="max_h:")
        self.max_slider_h_label.pack(side=tkinter.RIGHT)
        self.max_slider_l.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)
        self.max_slider_l_label = tkinter.Label(bottomframe0, text="max_l:")
        self.max_slider_l_label.pack(side=tkinter.RIGHT)
        self.min_slider_h.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)
        self.min_slider_h_label = tkinter.Label(bottomframe0, text="min_h:")
        self.min_slider_h_label.pack(side=tkinter.RIGHT)
        self.min_slider_l.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)
        self.min_slider_l_label = tkinter.Label(bottomframe0, text="min_l:")
        self.min_slider_l_label.pack(side=tkinter.RIGHT)
        self.min_slider_l.bind("<Return>", self.evaluate)
        self.min_slider_h.bind("<Return>", self.evaluate)
        self.max_slider_l.bind("<Return>", self.evaluate)
        self.max_slider_h.bind("<Return>", self.evaluate)

        full_ports = list(serial.tools.list_ports.comports())
        portnames = [item[0] for item in full_ports]

        if len(portnames) > 0:
            self.menuselect = tkinter.StringVar(self.root)
            self.menuselect.set(portnames[0])
            listboxdataconnect = tkinter.OptionMenu(
                *(self.root, self.menuselect) + tuple(portnames)
            )

            listboxdataconnect.pack(in_=bottomframe1,
                                    side=tkinter.LEFT,
                                    padx=3, pady=ypadding)

            self.reset_baselinebut = tkinter.Button(
                master=bottomframe1,
                text="Reset Baseline",
                command=self.reset_baseline
            )
            self.reset_baselinebut.pack(side=tkinter.RIGHT,
                                        padx=3, pady=ypadding)

            self.baselinebut = tkinter.Button(master=bottomframe1,
                                              text="Baseline",
                                              command=self.set_baseline)
            self.baselinebut.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

            self.recorddata = tkinter.Button(
                master=bottomframe1, text='Record', command=self.record)
            self.recorddata.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

            self.buttonconnect = tkinter.Button(
                master=bottomframe1, text='Connect', command=self.connect)
            self.buttonconnect.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)
        else:
            # no serial port detected.
            self.text.setvalue("no serial port found, hope that's OK")
            logger.info(self.text)
            tkinter.tkMessageBox.showwarning(
                "No serial port",
                "No device detected\nCheck cable and connection"
            )

        resetfilebut = tkinter.Button(bottomframe2, text='Reset File Marker',
                                      command=self.reset_file)
        resetfilebut.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

        readfilerunbut = tkinter.Button(bottomframe2, text='Run',
                                        command=self.run_file)
        readfilerunbut.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

        readfilebackbut = tkinter.Button(bottomframe2, text='Step Back',
                                         command=self.step_file_back)
        readfilebackbut.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

        readfilestartbut = tkinter.Button(bottomframe2, text='Step',
                                          command=self.step_file)
        readfilestartbut.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

        readfilebut = tkinter.Button(bottomframe2, text='Read from File',
                                     command=self.load_file)
        readfilebut.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

        # start Serial handler off in a separate process.
        self.s = OpenEIT.backend.Serialhandler(self._data_queue)
        self.text = 'hi'

        self.root.after(10, self.process_data)

        self.playback = None
        if initial_port is not None:
            if virtual_tty:
                with open(initial_port, "r") as file_handle:
                    self.playback = VirtualSerialPortPlayback(file_handle,
                                                              self)
            elif read_file:
                with open(initial_port, "r") as file_handle:
                    self.playback = FilePlayback(file_handle, self)
            else:
                self.menuselect.set(initial_port)
                self.connect()

    @property
    def text(self):
        return self._text.get()

    @text.setter
    def text(self, value):
        self._text.set(value)

    def disconnect(self):
        if self.playback is not None:
            self.playback.close()

        self.s.disconnect()

    def run(self):
        self.root.mainloop()

    def connect(self):
        if self.s.is_connected():
            self.s.disconnect()
            connectbuttontext = 'Connect'
        else:
            port_selection = self.menuselect.get()
            self.s.connect(port_selection)
            connectbuttontext = 'Disconnect'

        # GUI Update.
        self.buttonconnect.config(text=connectbuttontext)

    def update_cbar(self):
        # update the color bar with the min/maxes set as the slider.
        # Try to update this on the toplevel axes if they exist, as
        # well.

        # get slider values.
        min_cbar = self.w1.get()
        max_cbar = self.w2.get()
        if min_cbar < max_cbar:
            # redraw the cbar with new limits
            self.cbar = mpl.colorbar(self.plot,
                                     cax=self.cbaxes)
            self.cbar.set_clim([min_cbar, max_cbar])
            # if top window exists.
            if self.top is not None:
                if self.top.winfo_exists():
                    self.topcbar = mpl.colorbar(self.topplot,
                                                cax=self.topcbaxes)
                    self.topcbar.set_clim([min_cbar, max_cbar])

            self.update_figure()
        else:
            self.text = 'min has to be less than max for this to work.'
            logger.info(self.text)

    def record(self):
        if self.recording:
            # Connect
            recordbuttontext = 'Record'
            self.recording = True
        else:
            recordbuttontext = 'Stop Recording'
            self.recording = False
        self.recorddata.config(text=recordbuttontext)

    def update_figure(self):
        start_time = time.time()

        if self.top is None or not self.top.winfo_exists():
            # check if top window is open.
            self.plot.set_array(self.img-self._baseline)

            self.canvas.draw()
            self.canvas.flush_events()
        else:
            # If the top window is enabled, use it instead for updates.
            logger.debug('top window update')
            self.topplot.set_array(self.img-self._baseline)
            self.topcanvas.draw()
            self.topcanvas.flush_events()

        # We need time comparisons now.
        self.total_rendering_time += (time.time() - start_time)

        # self.text += ' render time:' + str(self.total_rendering_time)
        # if self.file_marker >= (len(self.data_file_array)-2):
        #       print 'total rendering time: ',self.total_rendering_time
        #       self.text += ' total: '+ str(self.total_rendering_time)
        # simplest thing to do with textbox is to keep everything the same no.
        # of characters.
        #
        # What do I want it to say?
        # when playing bak a file.
        # reading file... 1/84 total render: 3.443. total reconstruct: 5.442
        # Done.
        #
        # realtime buffer... 324873  total render: total reconstruct:
        #

    def process_data(self):
        try:
            self.img = self._image_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            logger.info("rendering new image ...")
            before = time.time()
            self.update_figure()
            self.text = 'render time: %.2f' % (
                time.time() - before)
            logger.info(self.text)
        self.root.after(10, self.process_data)

    def set_baseline(self):
        self._baseline = self.img
        self.update_figure()

    def reset_baseline(self):
        self._baseline = numpy.zeros((self.image_pixels, self.image_pixels),
                                     dtype=numpy.float)
        self.update_figure()

    def load_file(self):
        file_handle = tkinter.filedialog.askopenfile()

        if file_handle is None:
            return

        with file_handle:
            self.disconnect()
            self.playback = FilePlayback(file_handle, self)

    def step_file(self):
        if self.playback is not None:
            self.playback.step()

    def step_file_back(self):
        if self.playback is not None:
            self.playback.step_back()

    def run_file(self):
        if self.playback is not None:
            if self.playback.step():
                self.root.after(10, self.run_file)

    def reset_file(self):
        if self.playback is not None:
            self.playback.rewind()

    def About(self):
        print('Open Source Biomedical Imaging Project')

    def Eitwin(self):
        self.top = tkinter.Toplevel(master=self.root)
        self.top.title('EIT Reconstruction Window')
        fig = mpl.Figure(figsize=(5, 4), dpi=100)
        # pos = [left, bottom, width, height]
        image_position = [0.1, 0.25, 0.7, 0.7]
        colorbar_position = [0.85, 0.25, 0.03, 0.7]
        self.topimageplt = fig.add_axes(image_position)
        self.topcbaxes = fig.add_axes(colorbar_position)

        # 180,225,270,315,0,45,90,135
        # 1,2,3,4,5,6,7,8
        # Add text for electrode locations.
        self.topimageplt.annotate('180d(AFE1)',
                                  xy=(0.4, 0.9),
                                  xycoords='axes fraction')
        self.topimageplt.annotate('225d(AFE2)',
                                  xy=(0.15, 0.75),
                                  xycoords='axes fraction')
        self.topimageplt.annotate('270d(AFE3)',
                                  xy=(0.0, 0.5),
                                  xycoords='axes fraction')
        self.topimageplt.annotate('315d(AFE4)',
                                  xy=(0.2, 0.2),
                                  xycoords='axes fraction')
        self.topimageplt.annotate('0d(AFE5)',
                                  xy=(0.5, 0.1),
                                  xycoords='axes fraction')
        self.topimageplt.annotate('45d(AFE6)',
                                  xy=(0.75, 0.25),
                                  xycoords='axes fraction')
        self.topimageplt.annotate('90d(AFE7)',
                                  xy=(0.9, 0.5),
                                  xycoords='axes fraction')
        self.topimageplt.annotate('135d(AFE8)',
                                  xy=(0.8, 0.8),
                                  xycoords='axes fraction')

        self.topplot = self.topimageplt.imshow(self.img-self._baseline,
                                               interpolation='nearest')

        self.topcbar = mpl.colorbar(self.topplot,
                                    cax=self.topcbaxes)
        # self.cbar = mpl.pyplot.colorbar(self.imageplt,cax = self.cbaxes)
        scale_max = 90000
        min_cbar = 0
        max_cbar = scale_max
        self.topcbar.set_clim([min_cbar, max_cbar])
        #
        self.topcanvas = matplotlib.backends.backend_tkagg.FigureCanvasTkAgg(
            fig,
            master=self.top
        )
        self.topcanvas.show()
        self.topcanvas.get_tk_widget().pack(side=tkinter.TOP,
                                            fill=tkinter.BOTH,
                                            expand=1)
        toolbar = matplotlib.backends.backend_tkagg.NavigationToolbar2TkAgg(
            self.topcanvas,
            self.top
        )
        toolbar.update()
        self.topcanvas._tkcanvas.pack(side=tkinter.TOP,
                                      fill=tkinter.BOTH,
                                      expand=1)

    def Something_else(self):
        print('menu item')

    def quit(self):
        self.root.quit()     # stops mainloop
        self.root.destroy()  # this is necessary on Windows to prevent
        # Fatal Python Error: PyEval_RestoreThread: NULL tstate
        sys.exit()

    def evaluate(self, event):
        sliders = [self.min_slider_l.get(), self.min_slider_h.get(),
                   self.max_slider_l.get(), self.max_slider_h.get()]
        i = 0
        for value in sliders:
            if value != "":
                self.sliders[i] = int(value)
            i = i+1
        logger.debug('slider values', self.sliders)
        # # re-initialize the sliders ranges.
        self.w1.configure(from_=self.sliders[0], to=self.sliders[1])
        self.w2.configure(from_=self.sliders[2], to=self.sliders[3])

    def update_hist(self):
        self.plot.set_array(self.img-self._baseline)
        self.histplt.cla()
        flatimg = (self.img - self._baseline).flatten()
        n, bins, patches = self.histplt.hist(flatimg,
                                             bins='auto',
                                             facecolor='g')
        self.hist_update = False
        self.canvas.draw()
        self.canvas.flush_events()


if __name__ == "__main__":
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)
    logger = logging.getLogger(__name__)

    ap = argparse.ArgumentParser()

    ap.add_argument("-f", "--read-file",
                    action="store_true",
                    default=False)
    ap.add_argument("--virtual-tty",
                    action="store_true",
                    default=False)
    ap.add_argument("port", nargs="?")

    args = ap.parse_args()

    gui = Gui(
        initial_port=args.port,
        read_file=args.read_file,
        virtual_tty=args.virtual_tty,
    )
    gui.run()
