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
    {"random_selection_5" : "Random",
     "adaptive_selection_19" : "Linear",
     "adaptive_selection_20" : "Multiplicative"}

tests_to_plot = testname_2_title.keys()

def line2data(line):
    val1 = float(line.split(",")[0])
    val2 = float(line.split(",")[1])
    return [val1,val2]

def setBoxColors(bp):
    plt.setp(bp['boxes'][0], color='blue')
    plt.setp(bp['caps'][0], color='blue')
    plt.setp(bp['caps'][1], color='blue')
    plt.setp(bp['whiskers'][0], color='blue')
    plt.setp(bp['whiskers'][1], color='blue')
    plt.setp(bp['fliers'][0], color='blue')
    #plt.setp(bp['fliers'][1], color='blue')
    plt.setp(bp['medians'][0], color='blue')

    plt.setp(bp['boxes'][1], color='blue')
    plt.setp(bp['caps'][2], color='blue')
    plt.setp(bp['caps'][3], color='blue')
    plt.setp(bp['whiskers'][2], color='blue')
    plt.setp(bp['whiskers'][3], color='blue')
    plt.setp(bp['fliers'][1], color='blue')
    #plt.setp(bp['fliers'][2], color='blue')
    #plt.setp(bp['fliers'][3], color='blue')
    plt.setp(bp['medians'][1], color='blue')

    plt.setp(bp['boxes'][2], color='red')
    plt.setp(bp['caps'][4], color='red')
    plt.setp(bp['caps'][5], color='red')
    plt.setp(bp['whiskers'][4], color='red')
    plt.setp(bp['whiskers'][5], color='red')
    plt.setp(bp['fliers'][2], color='red')
    #plt.setp(bp['fliers'][4], color='red')
    #plt.setp(bp['fliers'][5], color='red')
    plt.setp(bp['medians'][2], color='red')

def get_boxes(testname):
    ip_to_datalines = {}
    for ip in svmips:
        data = open("%s/%s-qlens.dat" % (testname, ip), 'r').readlines()
        ip_to_datalines[ip] = reduce(lambda x, y: x + y, map(line2data, data))

    #hack
    assert odd_man_out == "10.61.192.165"
    oddvals = ip_to_datalines[odd_man_out]
    worker1vals = ip_to_datalines[svmips[0]]
    worker2vals = ip_to_datalines[svmips[1]]
    assert not worker1vals == odd_man_out
    assert not worker2vals == odd_man_out
    assert not worker2vals == worker1vals

    return [worker1vals, worker2vals, oddvals]

fig = plt.figure()
ax = plt.axes()
plt.hold(True)

pos = 1
xtick_labels = []
xticks = []
for t in testname_2_title.keys():
    xtick_labels.append(testname_2_title[t])
    xticks.append(pos + 0.2)

    bp = plt.boxplot(get_boxes(t), positions=[pos,pos+.5,pos+1], widths=0.3)
    pos += 3
    setBoxColors(bp)

ax.set_xticklabels(xtick_labels)
ax.set_xticks(xticks)
ax.set_xlim([-1,10])

# draw temporary red and blue lines and use them to create a legend
hB, = plt.plot([1,1],'b-')
hR, = plt.plot([1,1],'r-')
plt.legend((hB, hR),('Worker VM Node', 'Empty Node'))
hB.set_visible(False)
hR.set_visible(False)

plt.title("Realtime Queue Length Values (qlen ceiling = 100)")
plt.show()
