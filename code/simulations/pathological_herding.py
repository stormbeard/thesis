#
# Author: Tony Allen (cyril0allen@gmail.com)
#

import bisect
import math
import matplotlib.pyplot as plt
import numpy as np
import random
import time

# Number of times to perform selection on each set of disks.
selection_counts = [1000, 10000, 100000]

# Objects of ascending weight.
num_objects = 20
objects_w_weight = range(0, num_objects)
objects_w_weight.append(1000)

def gen_selection_counts(selection_func, iteration_count):
    selection_counters = len(objects_w_weight) * [0]
    for ii in range(iteration_count):
        selected = selection_func(objects_w_weight)[0]
        # Convert to an index.
        selected = objects_w_weight.index(selected)
        selection_counters[selected] += 1
    return selection_counters

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
    weight_sum = sum(lst)
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
    for i in lst:
        assert(i >= 0)
        if i == 0:
            r = 0
        else:
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
    num_selection_counts = len(selection_counts)
    for f in funcs:
        plt.figure()
        plt_counter = 0
        max_bar_size = 0
        for scounts in selection_counts:
            plt_counter += 1
            plt.subplot("13%d" % plt_counter)
            name = f.func_name
            print(name + " @ %d:" % scounts)
            selection_counters = gen_selection_counts(f, scounts)
            # Normalize the selection counters.
            norm_selection_counters = \
                map(lambda x: x / float(scounts), selection_counters)
            max_bar_size = max(max_bar_size, max(norm_selection_counters))
            print(str(norm_selection_counters))
            plot_data(name, scounts, norm_selection_counters)
        plt.ylim(0, max_bar_size)
        plt.show()

def plot_data(fname, n, selection_counters):
    plt.title("%s (n=%d)" % (fname, n))
    plt.xlabel("Object Weight")
    plt.ylabel("Normalized Selection Count")

    # This disgusting hack makes me cry.
    tmp = objects_w_weight
    tmp = map(lambda x: x if not x == 1000 else len(tmp) - 1, tmp)
    print("@tony %s, %s" % (objects_w_weight, selection_counters))
    s = map(lambda x: str(x), objects_w_weight)

    plt.bar(tmp, selection_counters, tick_label=s)

run_tests()
