#! /usr/bin/python
#
# Author: Tony Allen (cyril0allen@gmail.com)

import matplotlib.pyplot as plt
import numpy as np

svmips = ["10.61.192.108", "10.61.192.109", "10.61.192.110"]
odd_man_out = "10.61.192.110"
random_selection_test = "random_selection_2"
adaptive_selection_test = "adaptive_selection_6"

random_selection_map = {}
adaptive_selection_map = {}

def plot_from_map(svmip, selection_map):
    random_sz = len(selection_map[svmip])
    x = np.arange(random_sz)
    y = selection_map[svmip]
    plt.plot(x, y)

for i in svmips:
    # Adaptive test data.
    data = open(adaptive_selection_test + "/" + i + ".txt", 'r').readlines()
    usage_pcts = (
        map(lambda x: float(x.split(",")[1]) / float(x.split(",")[0]), data))
    adaptive_selection_map[i] = list(usage_pcts)

    # Random test data.
    data = open(random_selection_test + "/" + i + ".txt", 'r').readlines()
    usage_pcts = (
        map(lambda x: float(x.split(",")[1]) / float(x.split(",")[0]), data))
    random_selection_map[i] = list(usage_pcts)

adaptive_avg_fullness_primary = []
random_avg_fullness_primary = []
for ii in range(len(adaptive_selection_map[odd_man_out])):
    adaptive_avg_fullness_primary.append(
        (adaptive_selection_map["10.61.192.108"][ii] +
         adaptive_selection_map["10.61.192.109"][ii]) / 2.0)
for ii in range(len(random_selection_map[odd_man_out])):
    random_avg_fullness_primary.append(
        (random_selection_map["10.61.192.108"][ii] +
         random_selection_map["10.61.192.109"][ii]) / 2.0)

# Calculate deviation from the average fullness of the workload nodes.
a_dev = []
r_dev = []
for ii in range(len(adaptive_selection_map[odd_man_out])):
    a_dev.append(abs(adaptive_selection_map[odd_man_out][ii] -
                 adaptive_avg_fullness_primary[ii]))
for ii in range(len(random_selection_map[odd_man_out])):
    r_dev.append(abs(random_selection_map[odd_man_out][ii] -
                 random_avg_fullness_primary[ii]))

legend = []
legend.append("fitness selection")
plt.plot(range(len(a_dev)), a_dev)

legend.append("random selection")
plt.plot(range(len(r_dev)), r_dev)
plt.legend(legend, loc="bottom right")

plt.title("Idle Node Hot-tier Deviation")
plt.xlabel("Time")
plt.ylabel("% Deviation")
plt.show()
