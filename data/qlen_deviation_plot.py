#! /usr/bin/python
#
# Author: Tony Allen (cyril0allen@gmail.com)

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import math, sys

matplotlib.rcParams.update({'font.size': 22})

svmips = ["10.61.192.163", "10.61.192.164", "10.61.192.165"]
odd_man_out = "10.61.192.165"

testname_2_title = \
    {"random_selection_5" : "Random selection",
     "adaptive_selection_17" : "Adaptive selection, linear fitness",
     "adaptive_selection_18" : "Adaptive selection, multiplicative fitness"}

tests_to_plot = testname_2_title.keys()

def line2data(line):
    val1 = float(line.split(",")[0])
    val2 = float(line.split(",")[1])
    return val1 + val2

legend = []
def plot_test(testname, integrate):
    ip_to_datalines = {}
    for ip in svmips:
        data = open("%s/%s-qlens.dat" % (testname, ip), 'r').readlines()
        ip_to_datalines[ip] = map(line2data, data)

    #hack
    assert odd_man_out == "10.61.192.165"
    oddvals = ip_to_datalines[odd_man_out]
    worker1vals = ip_to_datalines[svmips[0]]
    worker2vals = ip_to_datalines[svmips[1]]
    assert not worker1vals == odd_man_out
    assert not worker2vals == odd_man_out
    assert not worker2vals == worker1vals

    # calculate the ydeviation
    ydeviation = []
    for idx in range(min(len(oddvals), len(worker1vals), len(worker2vals))):
        avg = (worker1vals[idx] + worker2vals[idx]) / 2.0
        ydeviation.append(avg - oddvals[idx])

    if integrate:
        # get integrated qlens
        yintegrated = []
        counter = 0
        total = 0
        for ii in ydeviation:
            if counter < 10:
                total += ii
                counter += 1
            else:
                yintegrated.append(total / 10.0)
                total = 0
                counter = 0

    if integrate:
        xvals = map(lambda x: 10*x, range(len(yintegrated)))
        plt.plot(xvals, yintegrated)
    else:
        xvals = map(lambda x: 10*x, range(len(ydeviation)))
        plt.plot(xvals, ydeviation)
    legend.append(testname_2_title[testname])

# Do the plotting
for t in testname_2_title.keys():
    plot_test(t, False)

plt.legend(legend)
plt.xlabel("Time (secs)")
plt.ylabel("Average Queue Length Deviation")
plt.title("Avg qlen data example")
plt.show()
