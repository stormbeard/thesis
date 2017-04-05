#
# Author: Tony Allen (cyril0allen@gmail.com)
#

import bisect
import math
import matplotlib.pyplot as plt
import numpy as np
import random
import time

""" Evaluate runtimes of various algorithms. """

# Number of times to perform selection on each set of disks.
selection_count = 10

# The number of items for selection.
num_disks_for_tests = range(1000,100000,5000)

print("Running selection tests %d times." % len(num_disks_for_tests))

# Map function to its avg runtimes for tuple (num disks, runtime secs).
runtime_map = {}

# Map a test to its std dev.
std_dev_map = {}

# Generate a list of average runtimes corresponding with 'num_disks_for_tests'.
def gen_runtimes(selection_func, iteration_count):
    runtimes = []
    std_devs = []
    # For each pool size.
    for pool_size in num_disks_for_tests:
        print("Measuring with pool size " + str(pool_size))
        runtime_list = []
        # Make a list of pool_size random numbers between 1 and 10.
        lst = pool_size * [1]
        # Time selections and get the average runimes.
        for it in range(iteration_count):
            start_time = time.time()
            selection_func(lst)
            elapsed_time = time.time() - start_time
            runtime_list.append(elapsed_time)
        avg_runtime = np.average(runtime_list)
        std_dev = np.std(runtime_list)
        runtimes.append(avg_runtime)
        std_devs.append(std_dev)
    return runtimes, std_devs


"""
Selection algorithms (choosing 3)
"""
def random_selection(lst):
    ret = []
    ret.append(lst[random.randint(0,len(lst)-1)])
    ret.append(lst[random.randint(0,len(lst)-1)])
    ret.append(lst[random.randint(0,len(lst)-1)])
    return ret

def roullette_wheel(lst):
    weight_sum = len(lst)
    ret = []
    for times in range(3):
        rand_num = random.randint(0, weight_sum - 1)
        runner = 0
        for i in lst:
            runner += i
            if runner > rand_num:
                ret.append(i)
                break
    assert(len(ret) == 3)
    return ret

def truncation_selection(lst):
    # Determine top 10%.
    top_t = []
    for i in lst:
        bisect.insort(top_t, i)
        if len(top_t) > len(lst) / 10:
            top_t.pop(0)
    ret = []
    ret.append(top_t[random.randint(0, len(top_t) - 1)])
    ret.append(top_t[random.randint(0, len(top_t) - 1)])
    ret.append(top_t[random.randint(0, len(top_t) - 1)])
    return ret

def weighted_reservoir(lst):
    """
    Give up at the halfway point of the list.
    """
    pqueue = []
    for i in lst[:len(lst)/2]:
        r = random.random() ** (1/i)
        if len(pqueue) < 3:
            bisect.insort(pqueue, i)
        else:
            pqueue.pop(0)
            bisect.insort(pqueue, i)
    return pqueue

def two_choice(lst):
    ret = []
    for i in range(3):
        choice1 = lst[random.randint(0,len(lst)-1)]
        choice2 = lst[random.randint(0,len(lst)-1)]
        ret.append(max(choice1, choice2))
    return ret

"""
Run tests
"""
funcs = [random_selection,
         roullette_wheel,
         truncation_selection,
         weighted_reservoir,
         two_choice]

def run_tests():
    for f in funcs:
        name = f.func_name
        print(name + ":")
        runtimes, std_devs = gen_runtimes(f, selection_count)
        print(str(runtimes))
        runtime_map[name] = runtimes
        std_dev_map[name] = std_devs

def plot_data():
    plt.figure()
    plt.title("Selection Algorithm Scalability (n=%d)" % selection_count)
    plt.xlabel("Selection Set Size")
    plt.ylabel("Run Time (secs)")
    ax = plt.subplot()
    ax.set_yscale("log")
    ax.set_xscale("log")
    legend = []
    for fname in map(lambda x: x.func_name, funcs):
        # Std error is (std_dev / sqrt(num_samples)).
        std_errors = map(lambda e: e / math.sqrt(selection_count),
                         std_dev_map[fname])
        plt.errorbar(num_disks_for_tests, runtime_map[fname],
                     yerr=std_errors)
        legend.append(fname)
    plt.legend(legend, loc='upper_left')
    plt.show()

run_tests()
plot_data()
