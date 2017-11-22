import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

dataX = np.array([1,2,3,4,5,6,7,8,9,10])
dataY = np.array([1193,1225,1125,1644,1255,13676,2007,2008,12359,1210])

ax = plt.subplot(111)
def on_click(event):
    if event.dblclick:
       ax.plot((event.xdata, event.xdata), (mean-standardDeviation, mean+standardDeviation), 'r-')
       plt.show()

def _yes(event):
    print("yolo")

mean = np.mean(dataY)
standardDeviation = np.std(dataY)

ax.plot(dataX, dataY, linewidth=0.5)
plt.connect('button_press_event', on_click)

axcut = plt.axes([0.9, 0.0, 0.1, 0.075])
bcut = Button(axcut, 'YES', color='red', hovercolor='green')
bcut.on_clicked(_yes)

plt.show()