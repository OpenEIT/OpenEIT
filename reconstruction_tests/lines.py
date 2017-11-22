import matplotlib.pyplot as plt
import numpy as np
import math

# create the figure
fig = plt.figure(figsize=(8,8))
ax = fig.add_subplot(111,aspect='equal')  

# theta goes from 0 to 2pi
theta = np.linspace(0, 2*np.pi, 100)
# the radius of the circle
r = np.sqrt(9)
# compute x1 and x2
x1 = r*np.cos(theta)
x2 = r*np.sin(theta)
ax.plot(x1, x2)


# 
theta_points=[0,np.pi/4,np.pi/2,3*np.pi/4,np.pi,5*np.pi/4,3*np.pi/2,7*np.pi/4]
n1 = r*np.cos(theta_points)
n2 = r*np.sin(theta_points)
ax.plot(n1,n2,'or')
for i,j in zip(n1, n2):
    ax.annotate('%s)' %j, xy=(i,j), xytext=(30,0), textcoords='offset points')
    ax.annotate('(%s,' %i, xy=(i,j))

# change default range so that new circles will work
ax.set_xlim((-5, 5))
ax.set_ylim((-5, 5))


ax.set_aspect(1)
plt.grid()
plt.show()





# plt.plot([1,2,3,4], [1,4,9,16], 'ro')
# plt.axis([0, 6, 0, 20])
# plt.show()