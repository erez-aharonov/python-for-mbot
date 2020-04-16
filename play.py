from lib.mbot2 import Robot
from matplotlib import pyplot as plt
import numpy as np

robot = Robot()
# plt.figure()
#
# x = []
#
# while True:
#     value = robot.request_line_follower(1, 2)
#     print(value)
#     x.append(value)
#     plt.plot(x)
#     plt.draw()
#
# # plt.show()
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import random

import time

fig = plt.figure()
ax1 = fig.add_subplot(1,1,1)


def animate(i):
    value = robot.request_line_follower(1, 2)
    dataArray = [[1,2],[2,3],
[3,6],
[4,9],
[5,4],
[6,7],
[7,7],
[8,4],
[9,3],
[10,7]]
    # dataArray = pullData.split('\n')
    xar = []
    yar = []
    for eachLine in dataArray:
        if len(eachLine)>1:
            x,y = eachLine
            xar.append(int(x) * value)
            yar.append(int(y) * value)
    ax1.clear()
    ax1.plot(xar,yar)
ani = animation.FuncAnimation(fig, animate, interval=1000)
plt.show()