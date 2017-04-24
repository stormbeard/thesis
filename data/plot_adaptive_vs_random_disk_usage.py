#! /usr/bin/python
#
# Author: Tony Allen (cyril0allen@gmail.com)

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rcParams.update({'font.size': 22})

svmips = ["10.61.192.108", "10.61.192.109", "10.61.192.110"]
odd_man_out = "10.61.192.110"
#tests_to_plot = ["random_selection_3",
#                 "adaptive_selection_7",
#                 "adaptive_selection_8"]

tests_to_plot = ["adaptive_selection_9",
                 "adaptive_selection_10",
                 "random_selection_4"]

# Map from test to map from svm ip to fullness timeseries
selection_maps = {}

def plot_from_map(svmip, selection_map):
    random_sz = len(selection_map[svmip])
    x = np.arange(random_sz)
    y = selection_map[svmip]
    plt.plot(x, y)

# Calculate pct usages.
for test in tests_to_plot:
    selection_maps[test] = {}
    for i in svmips:
        # Adaptive test data.
        data = open(test + "/" + i + "-tier_usage.txt",
                    'r').readlines()
        usage_pcts = (
            map(lambda x: 100 * float(x.split(",")[1]) / float(x.split(",")[0]),
                data))
        selection_maps[test][i] = list(usage_pcts)

# Get the disk fullness values for each node.
fullness_primaries = {}
for test in tests_to_plot:
    minrange = min(map(lambda x: len(x), selection_maps[test].values()))
    print "minrange: " + str(minrange)
    fullness_primaries[test] = []
    # Calculate the average non-oddman fullness.
    for ii in range(minrange):
        non_oddman_total = 0
        for ip, fullness_series in selection_maps[test].iteritems():
            if ip == odd_man_out:
                continue
            non_oddman_total += fullness_series[ii]
        fullness_primaries[test].append(float(non_oddman_total) /
                                        (len(svmips) - 1))

# Calculate deviation from the average fullness of the workload nodes.
deviations = {}
for test in tests_to_plot:
    deviations[test] = []
    minrange = min(map(lambda x: len(x), selection_maps[test].values()))
    for ii in range(minrange):
        deviations[test].append(abs(selection_maps[test][odd_man_out][ii] -
                                fullness_primaries[test][ii]))

legend = []
for test in tests_to_plot:
    legend.append(test)
    # TODO: make this in real time units via some map
    plt.plot(range(len(deviations[test])), deviations[test])

plt.legend(legend)
plt.title("Idle Node Hot-tier Deviation")
plt.xlabel("Time (arbitrary units)")
plt.ylabel("% Deviation")
plt.show()
