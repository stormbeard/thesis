#! /usr/bin/python
#
# Author: Tony Allen (cyril0allen@gmail.com)

import matplotlib.pyplot as plt
import numpy as np

svmips = ["10.61.192.108", "10.61.192.109", "10.61.192.110"]
adaptive_selection_test = "adaptive_selection_6"

adaptive_selection_map = {}

def plot_from_map(svmip, selection_map):
    random_sz = len(selection_map[svmip])
    x = np.arange(random_sz)
    y = selection_map[svmip]
    plt.plot(x, y)

legend = []
for i in svmips:
    data = open(adaptive_selection_test + "/" + i + ".txt", 'r').readlines()
    usage_pcts = (
        map(lambda x: float(x.split(",")[1]) / float(x.split(",")[0]), data))
    adaptive_selection_map[i] = list(usage_pcts)
    plot_from_map(i, adaptive_selection_map)
    legend.append(i)

plt.legend(legend, loc='bottom right')
plt.show()
