
import sys
import matplotlib
matplotlib.use("TkAgg")
from matplotlib import pyplot as plt
import argparse
import logging
import queue
import time
import tkinter
import serial.tools.list_ports
import OpenEIT.dashboard
import numpy
import configparser
# plt.use('Qt4Agg')
# 
logger = logging.getLogger(__name__)

# TODO: Improve State Feedback
# The current connection and playback state should be clearly visible
# at all times
# Read from Config
# enable 3 different GUI options. 
# 
# 
class Meshgui(object):

    def __init__(self, controller):

        self.controller = controller
        self.root = tkinter.Tk()
        self.root.bind("<Destroy>", lambda _: controller.shutdown() or True)
        self.root.wm_title("EIT Test Bench Dashboard")
        self.top = None
        self.topplot = None
        self.topcanvas = None
        self.topcbar = None
        self.topcbaxes = None

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

        #### 
        # Matplotlibbing.
        fig = plt.Figure(figsize=(5, 4), dpi=100)

        # pos = [left, bottom, width, height]
        image_position = [0.1, 0.25, 0.7, 0.7]
        histogram_position = [0.1, 0.08, 0.8, 0.1]
        colorbar_position = [0.85, 0.25, 0.03, 0.7]
        self.imageplt = fig.add_axes(image_position)
        self.histplt = fig.add_axes(histogram_position)
        self.cbaxes = fig.add_axes(colorbar_position)

        ypadding = 10
        # Will this often need to be changed?
        scale_max = 1.0
        scale_min = -1.0
        self.sliders = [-1.0, scale_max, -1.0, scale_max]
        self.min_cbar = 0
        self.max_cbar = scale_max
        scale_tick_interval = float(scale_max)/10
        """
        
        SET UP pyEIT plots for different algorithms. 
        GREIT gives a 32/32 pixel output, JAC and BP give a mesh. 

        """
        self.n_el = self.controller.n_el
        self.algorithm = self.controller.algorithm
        self.x,self.y,self.tri,self.el_pos = self.controller.plot_params()

        if self.algorithm == 'bp' or self.algorithm == 'jac':
            self.img = numpy.zeros(680)
            self.plot = self.imageplt.tripcolor(self.x,self.y, self.tri, self.img,
                 shading='flat', alpha=0.90, cmap=plt.cm.viridis,vmin=self.min_cbar,vmax=self.max_cbar)
            self.imageplt.set_aspect('equal')
            self.cbar = plt.colorbar(self.plot, cax=self.cbaxes)
            # draw electrodes. 
            self.imageplt.plot(self.x[self.el_pos], self.y[self.el_pos], 'ro')
            for i, e in enumerate(self.el_pos):
                self.imageplt.text(self.x[e], self.y[e], str(i+1), size=12)
          
        elif self.algorithm  == 'greit':
            self.gx,self.gy,self.ds = self.controller.greit_params()
            self.img = self.ds # numpy.zeros((32,32),dtype=float)
            xv = self.gx[0]   
            yv = self.gy[:, 0] 
            image = self.img.reshape(self.gx.shape)         
            fill = numpy.ones(680)
            self.plot = self.imageplt.pcolorfast(xv, yv, image, alpha=0.90, cmap=plt.cm.viridis,vmin=0,vmax=1)
            self.imageplt.tripcolor(self.x, self.y, self.tri, fill, alpha=0.10, cmap=plt.cm.gray,vmin=0, vmax=1)
            # draw electrodes. 
            self.imageplt.plot(self.x[self.el_pos], self.y[self.el_pos], 'ro')
            for i, e in enumerate(self.el_pos):
                self.imageplt.text(self.x[e], self.y[e], str(i+1), size=12)
            self.imageplt.set_aspect('equal')
            self.cbar = plt.colorbar(self.plot, cax=self.cbaxes)


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
        # canvas.plt_connect('key_press_event', on_key_event)
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
                                resolution = scale_tick_interval,
                                orient=tkinter.HORIZONTAL,
                                label='MIN',
                                command=self.update_cbar)
        self.w1.set(scale_max/10)
        self.w1.pack(fill="x", expand=True)
        self.w2 = tkinter.Scale(bottomframe0, from_=self.sliders[2],
                                to=self.sliders[3], length=600,
                                tickinterval=scale_tick_interval,
                                resolution = scale_tick_interval,
                                orient=tkinter.HORIZONTAL,
                                label='MAX',
                                command=self.update_cbar)
        self.w2.set(9*scale_max/10)
        self.w2.pack(fill="x", expand=True)

        # Text entry boxes for min and max range of each slider bar.
        cbarbut = tkinter.Button(bottomframe0, text='Update HIST',
                                 command=self.update_hist)
        cbarbut.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

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

            self.autoscalebut = tkinter.Button(
                master=bottomframe1,
                text="Autoscale",
                command=self.autoscale
            )
            self.autoscalebut.pack(side=tkinter.RIGHT,
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
                master=bottomframe1, text='Record',
                command=self.controller.start_recording
            )
            self.recorddata.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)
            self.controller.register(
                "recording_state_changed",
                self.on_record_state_changed
            )

            self.buttonconnect = tkinter.Button(
                master=bottomframe1, text='Connect',
                command=self.connect
            )
            self.controller.register(
                "connection_state_changed",
                self.on_connection_state_changed
            )
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
                                      command=self.controller.reset_file)
        resetfilebut.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

        readfilerunbut = tkinter.Button(bottomframe2, text='Run',
                                        command=self.run_file)
        readfilerunbut.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

        readfilebackbut = tkinter.Button(bottomframe2, text='Step Back',
                                         command=self.controller.step_file_back)
        readfilebackbut.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

        readfilestartbut = tkinter.Button(bottomframe2, text='Step',
                                          command=self.controller.step_file)
        readfilestartbut.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

        readfilebut = tkinter.Button(bottomframe2, text='Read from File',
                                     command=self.load_file)
        readfilebut.pack(side=tkinter.RIGHT, padx=3, pady=ypadding)

        self.text = 'hi'

        self.root.after(10, self.process_data)

    @property
    def text(self):
        return self._text.get()

    @text.setter
    def text(self, value):
        self._text.set(value)

    def run(self):
        self.root.mainloop()

    def connect(self):
        self.controller.connect(self.menuselect.get())

    def on_connection_state_changed(self, connected):
        if connected:
            self.buttonconnect.config(
                text='Disconnect',
                command=self.controller.disconnect
            )
        else:
            self.buttonconnect.config(
                text='Connect',
                command=self.connect
            )

    def on_record_state_changed(self, recording):
        if recording:
            self.recorddata.config(
                text="Stop Recording",
                command=self.controller.stop_recording,
            )
        else:
            self.recorddata.config(
                text="Record",
                command=self.controller.start_recording,
            )

    def update_cbar(self, *args):
        # get slider values.
        self.min_cbar = self.w1.get()
        self.max_cbar = self.w2.get()
        # check that's displayed to screen. 
        if self.min_cbar >= self.max_cbar:
            self.text = 'min has to be less than max for this to work.'
            logger.info(self.text)
            return

        self.plot.set_clim([self.min_cbar, self.max_cbar])
        self.cbar.update_normal(self.imageplt)

        # if top window exists.
        if self.top is not None:
            if self.top.winfo_exists():
                self.topplot.set_clim([self.min_cbar, self.max_cbar])
                self.topcbar.update_normal(self.topplot)

        self.update_figure()

    def update_figure(self):
        start_time = time.time()
        # check if top window is open.
        if self.top is None or not self.top.winfo_exists():

            if self.algorithm == 'bp' or self.algorithm == 'jac':
                self.imageplt.tripcolor(self.x,self.y, self.tri, self.img,
                     shading='flat', alpha=0.90, cmap=plt.cm.viridis,vmin=self.min_cbar,vmax=self.max_cbar)
            elif self.algorithm  == 'greit':
                try:         
                    xv = self.gx[0]
                    yv = self.gy[:, 0]
                    image = self.img.reshape(self.gx.shape) 
                    self.imageplt.pcolorfast(xv,yv, image, alpha=0.9 , cmap=plt.cm.viridis,vmin=self.min_cbar,vmax=self.max_cbar)
                except NameError: 
                    print ('img not defined')
            else: 
                print ('couldnt find the algorithm')
            self.canvas.draw()
            self.canvas.flush_events()
        else:
            # If the top window is enabled, use it instead for updates.
            logger.debug('top window update')

            if self.algorithm == 'bp' or self.algorithm == 'jac':
                print ('updating bp')
                # self.topplot = self.topimageplt.
                self.topimageplt.tripcolor(self.x,self.y, self.tri, self.img,
                     shading='flat', alpha=0.90, cmap=plt.cm.viridis,vmin=self.min_cbar,vmax=self.max_cbar)
            elif self.algorithm  == 'greit':
                try:         
                    xv = self.gx[0]
                    yv = self.gy[:, 0]
                    image = self.img.reshape(self.gx.shape) 
                    self.topimageplt.pcolorfast(xv,yv, image, alpha=0.9 , cmap=plt.cm.viridis,vmin=self.min_cbar,vmax=self.max_cbar)
                except NameError: 
                    print ('img not defined')
            else: 
                print ('couldnt find the algorithm')

            # self.topcanvas.blit(self.topplot)
            self.topcanvas.draw()
            self.topcanvas.flush_events()

        self.total_rendering_time += (time.time() - start_time)

    def process_data(self):
        try:
            self.img = self.controller.image_queue.get_nowait()
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
        self.controller.baseline(data)
        self.update_figure()

    def reset_baseline(self): # This sets baseline to what was originally stored in the background.txt file. 
        self.controller.reset_baseline()
        self.update_figure()

    def load_file(self):

        try:
            file_handle = tkinter.filedialog.askopenfile()
            logger.info(file_handle)
        except RuntimeError as err:
            logger.error('problem opening file dialog: %s', err)

        if file_handle is None:
            print ('didnt get the file!')
            return

        with file_handle:
            self.controller.load_file(file_handle)

    def run_file(self):
        if self.controller.step_file():
            self.root.after(10, self.run_file)


    def About(self):
        print('Open Source Biomedical Imaging Project')

    def Eitwin(self):
        self.top = tkinter.Toplevel(master=self.root)
        self.top.title('EIT Reconstruction Window')
        fig = plt.Figure(figsize=(5, 4), dpi=100)
        # pos = [left, bottom, width, height]
        image_position = [0.1, 0.25, 0.7, 0.7]
        colorbar_position = [0.85, 0.25, 0.03, 0.7]
        self.topimageplt = fig.add_axes(image_position)
        self.topcbaxes = fig.add_axes(colorbar_position)

        if self.algorithm == 'bp' or self.algorithm == 'jac':
            print ('bp in top plot')
            self.img = numpy.zeros(680)
            self.topplot = self.topimageplt.tripcolor(self.x,self.y, self.tri, self.img,
                 shading='flat', alpha=0.90, cmap=plt.cm.viridis,vmin=self.min_cbar,vmax=self.max_cbar)
            self.topimageplt.set_aspect('equal')
         
        elif self.algorithm  == 'greit':
            print ('greit in top plot')
            self.img = self.ds # numpy.zeros((32,32),dtype=float)
            xv = self.gx[0]   
            yv = self.gy[:, 0] 
            image = self.img.reshape(self.gx.shape)         
            fill = numpy.ones(680)
            self.topplot = self.topimageplt.pcolorfast(xv, yv, image, alpha=0.90, cmap=plt.cm.viridis,vmin=0,vmax=1)
            self.topimageplt.set_aspect('equal')


        self.topcbar = plt.colorbar(self.topplot,
                                    cax=self.topcbaxes)
        # self.cbar = plt.pyplot.colorbar(self.imageplt,cax = self.cbaxes)
        scale_max = 1
        self.min_cbar = 0
        self.max_cbar = scale_max
        self.topcbar.set_clim([self.min_cbar, self.max_cbar])
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
                self.sliders[i] = float(value)
            i = i+1
        logger.debug('slider values', self.sliders)
        # # re-initialize the sliders ranges.
        self.w1.configure(from_=self.sliders[0], to=self.sliders[1])
        self.w2.configure(from_=self.sliders[2], to=self.sliders[3])
        # scale_tick_interval = float(scale_max)/10
        self.w1.configure(resolution= (self.sliders[1]-self.sliders[0])/10,tickinterval=(self.sliders[1]-self.sliders[0])/10 )
        self.w2.configure(resolution= (self.sliders[3]-self.sliders[2])/10,tickinterval=(self.sliders[3]-self.sliders[2])/10 )

    def update_hist(self):

        nanless = self.img[~numpy.isnan(self.img)]

        self.histplt.cla()
        flatimg = (nanless).flatten()
        n, bins, patches = self.histplt.hist(flatimg,
                                             bins='auto',
                                             facecolor='g')
        self.canvas.draw()
        self.canvas.flush_events()


    def autoscale(self): # This sets baseline to what was originally stored in the background.txt file. 
        
        nanless = self.img[~numpy.isnan(self.img)]
        cmax= float(int(numpy.max(nanless)*100))/100.0
        cmin =float(int(numpy.min(nanless)*100))/100.0
        # print (cmin,cmax)
        # Set new min and maxes on the cbar, based on self.img min and max. 
        self.min_cbar = cmin
        self.max_cbar = cmax
        # update the image and the color bar. 
        if self.min_cbar >= self.max_cbar:
            self.text = 'min has to be less than max for this to work.'
            logger.info(self.text)
            return
        self.plot.set_clim([self.min_cbar, self.max_cbar])
        self.cbar.update_normal(self.imageplt)
        # if top window exists.
        if self.top is not None:
            if self.top.winfo_exists():
                self.topplot.set_clim([self.min_cbar, self.max_cbar])
                self.topcbar.update_normal(self.topplot)

        sliders = [self.min_cbar, self.max_cbar,
                   self.min_cbar, self.max_cbar]
        i = 0
        for value in sliders:
            if value != "":
                self.sliders[i] = float(value)
            i = i+1

        # update the sliders based on the current image. 
        self.w1.configure(from_=self.sliders[0], to=self.sliders[1])
        self.w2.configure(from_=self.sliders[2], to=self.sliders[3])
      
        self.w1.configure(resolution= (self.sliders[1]-self.sliders[0])/10,tickinterval=(self.sliders[1]-self.sliders[0])/10 )
        self.w2.configure(resolution= (self.sliders[3]-self.sliders[2])/10,tickinterval=(self.sliders[3]-self.sliders[2])/10 )

        self.w1.set(cmin)
        self.w2.set(cmax)

        self.update_figure()