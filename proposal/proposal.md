### Proposal for a Thesis in the Field of Information Technology
#### For Partial Fulfillment of Requirements For a Master of Liberal Arts Degree

#### Harvard University Extension School
#### Submission Date

#### Cyril Allen
500 N. Duke St.

Apt. 55-305

Durham, NC 27701

[cyril0allen@gmail.com](mailto:cyril0allen@gmail.com)

Tentative Thesis Title
----------------------
TODO

Abstract
--------

TODO

Introduction
------------

With the advent of cloud computing, datacenters are making use of distributed
applications more than ever. Companies like Google use software such as
MapReduce to generate over 20 petabytes of data per day using very large
numbers of commodity servers [3]. Many other companies use large scale clusters
to perform various computational tasks via the the open-source MapReduce
implementation, Hadoop [4], or they can possess a virtualized datacenter
allowing them to migrate virtual machines between various machines for
high-availability reasons. As economics change for hardware, it is likely a
scalable cloud will have the requirement to mix node types, which will lead to
higher performance/capacity nodes being mixed with lower performance (e.g.:
SATA SSD w/ NVMe SSD) and capacity HDD nodes.

Today, many applications such as MapReduce or the Nutanix file system, assume
homogeneous constituents due to their random data placement strategies. Not all
machines are equal, so one cannot expect for MapReduce tasks to be completed at
the same time, or high performance Nutanix file system writes to be as fast as
they would be in a homogeneous cluster. It has been shown that having a
platform which proactively balances the workload based on node capabilities can
improve performance [5][6][7][8]. In this paper, I propose an adaptive data
placement implementation for the Nutanix file system, aiming to improve
performance in heterogeneous clusters using the NDFS.

The Nutanix Distributed Filesystem
==================================

TODO

Related Work
============

Xie et. al. showed that data placement schemes based on the computing
capacities of nodes in the Hadoop Distributed File System (HDFS) [5]. These
computing capacities are determined for each node in the cluster by profiling a
target application leveraging the HDFS. Their MapReduced wordcount and grep
results showed up to a 33.1% reduction in response time. Similarly, Perez et.
al. applied adaptive data placement features to the Expand parallel file system
based on available free space [8]. Though effective in their given contexts,
the main drawback to this work is that it assumes the specific application is
working without interference and does not account for other workloads on the
system.

One adaptive data placement approach that can account for other workloads on
the system was introduced by Jin et. al. in their work on ADAPT [7]. The work
predicts how failure-prone a node in a MapReduce cluster is and advises their
availability-aware data placement algorithm to avoid those nodes. This proves
useful for performance by avoiding faulty nodes that could fail mid-task and
cause data transfers and re-calculation of data.


Thesis Project Description
--------------------------

Motivation
==========

TODO: Customer use-cases

Adaptive Data Placement
=======================

To remedy the problems that arise from hetereogeneous cluster configurations
discussed in the previous section, I plan to implement an adaptive replica
placement algorithm for the Nutanix distributed filesystem. This algorithm uses
a "fitness value" that is calculated from various statistics available for each
disk such as disk fullness and queue depth. These fitness values are to be used
to rank each disk when selecting where the Stargate will place data. This
should mitigate many problems seen with heterogeneous Nutanix clusters.

### Disk Stats Aggregation

TODO

### Selection Algorithms

TODO: Clean up and cite

#### Trucation Selection

This boils down to eliminating some proportion of the least fit elements in the
set and "breeding" the high fitness elements in a genetic algorithm context.
For our use case, we would just perform a random selection from the high
fitness disks. I believe this was discussed in a call a few weeks back and we
decided against it because the lowest fitness disks are never utilized. 

#### Stochastic Universal Sampling (SUS)

For this, let's just think of an example where some element has a 5%
probability of being chosen. On some roulete wheel with 100 bins, 5 of those
bins are for our example object. The algorithm steps through the wheel with a
randomly chosen interval and reports back with the set of objects landed on.
This isn't a good idea for us because some disks may not have stats yet and
would have a fitness value of 1. Other disks may have fitness values as high as
2000 and if they are not able to be chosen for some reason, we could subdivide
our roulette wheel so much that it would slow us down by a lot. We also have no
way to enforce exclusions outside of exclusion sets. I'm personally not a fan
of this one.

#### Tournament Selection

This looks something like:

* Randomly choose some subset of the total elements in our set.
* Find the most fit elements in the randomly chosen subset and return those with some probability (usually 1.0). We still run into the problem of exclusions mentioned above and if we can't find a useable candidate in the randomly chosen subset, we would have to perform this whole tournament again. Also, this method is highly specialized for selecting a set of objects. 

#### Fitness Proportionate Selection (FPS)

This is exactly what we're doing in DrawLottery() inside of our
/util/misc/random.h. It's worth noting that DrawLottery() is O(N) because of
the sequential search that looks something like:

* Calculate uniform random number in [0, weight_sum].
* Sequentially march through the weight vector provided and add numbers together until the current sum is >= the uniform random number. 

There is a variation on this mentioned in the wiki that can drop us down to
O(log(n)) by preprocessing a cumulative density function in some vector and
performing a binary search. Since the WeightedVector class doesn't allow for
removal of elements, we could simply append to the CDF vector each time a new
object is added. My concern here is that to manage exclusions, we would still
need to either constantly recalculate the CDF after each sample or keep
sampling while maintaining an exclusion set. The former will burn through CPU
cycles and the latter can take a very long time in the pathological case of a
fitness_value=1 disk being the only valid candidate. Also, Jaya's initial
concern that sparked this whole thing (do we need multiple vectors?) is still
there, we'd need a CDF vector as well as a weight vector (unless we want to
keep recalculating the fitness of each object).

There is also an O(1) optimization using the alias method, but this:

* Doesn't address Jaya's concern of multiple vectors since we would need both a probability table AND an alias table.
* Is expensive. The two tables need to be rebuilt for each addition to the WeightedVector and each recalculation of fitness values (5 secs right now). 

##### Stochastic Acceptance

A much simpler variation on the standard FPS algorithm is a "stochastic
acceptance" method where we just loop through all objects in the set and choose
one with a probability of (fitness_value / fitness_value_sum). This is great
for constantly changing fitness values, but would still require an exclusion
set and could take a long time in the pathological fitness=1 case mentioned a
few times. 

Testing and Benchmarks
======================

### Testing Replica Selection via Synthetic Workload Generation

Do determine the viability of various fitness function parameters in different
heterogeneous cluster topologies, I will need repeatedly simulate specific
workloads on varying hardware configurations. A tool must be written to deploy
virtual machines on each node in the cluster and run a workload similar to
those that can be found in real production systems. 

The exact APIs used for deployment of virtual machines will vary based on the
host hypervisor. The Nutanix Acropolis hypervisor exposes a REST API, which
will allow the freedom in tools development to write code in almost any
language. However, the Acropolis REST API is poorly documented and does not
have many examples on usage. On the other hand, VMware's ESXi hypervisor
exposes a Python library (PyVMomi) which allows for complete automation of
virtual machine deployment and configuration. PyVMomi is very well documented
and has multiple community samples, but the choice in programming language will
be strictly limited to Python.

Once a virtual machine is deployed, it must generate I/O in a configurable
manner. For this, I will use fio, a tool that wil spawn a number of threads or
processes to generate I/O. This will allow for repeatability of various
workloads with specific read/write ratios, queue depths, run times, and working
sets. My tool will connect to each virtual machine simultaneously via SSH and
run the fio script corresponding to the desired workload.

After the fio scripts have finished running, the workload generation tool must
aggregate various performance statistics gathered by the fio processes running
on each virtual machine. This can then be analyzed at a later time after the
clusters are torn down.

Hardware Requirements
---------------------

The replica placement scheme proposed earlier can be tested and verified using
an exhaustive battery of software tests. However, we still require real
hardware for the performance testing of synthetic workloads in heterogeneous
clusters. If we are to verify that the proposed work will not introduce a
performance regression in existing configurations and also improve performance
in current troublesome scenarios, we will need to create multiple different
hardware configurations.

The hardware required for each problem is shown the table below:

| Problem to Test | Required Hardware |
| ------------- |:-------------:|
| Homogeneous cluster regression tests | 4x identical Nutanix/Dell/Lenovo nodes |
| Storage-only node performance | Storage-only Nutanix nodes |
| Heterogeneous hybrid cluster performance | 1x weak hybrid node, 2x strong hybrid node |
| Heterogeneous hybrid and all flash cluster performance | 1x all-flash node, 2x any hybrid node |

Software Requirements
---------------------

All software requirements are satisfied by the Nutanix development environment.
This includes:

* The unit test infrastructure for replica selection simulations. This allows for quick prototyping of schemes.
* fio
* Tools for development of a workload generation tool for benchmarking and usage of real disk stats.

Benchmarks and Performance Analysis Methodology
-----------------------------------------------



Preliminary Schedule
--------------------
| Task          | Time in Weeks |
| ------------- |:-------------:|
| TODO 1        | 1 week        |
| TODO 2        | 2 weeks       |
| TODO 3        | 3 weeks       |

Bibliography
------------
 TODO: format the ciations correctly

1. Poitras, S. (2015, November 11). The Nutanix Bible - NutanixBible.com.
Retrieved February 15, 2016, from http://nutanixbible.com/

2.  Lakshman, A., & Malik, P. (2008, August 25). Cassandra – A structured storage system on a P2P Network. Retrieved February 15, 2016, from https://www.facebook.com/notes/facebook-engineering/cassandra-a-structured-storage-system-on-a-p2p-network/24413138919/

3. Dean, J., & Ghemawat, S. (2008). MapReduce: simplified data processing on large clusters. Communications of the ACM, 51(1), 107-113.

4. hadoop.apache.org # TODO: fix this

5. Xie, J., Yin, S., Ruan, X., Ding, Z., Tian, Y., Majors, J., ... & Qin, X. (2010, April). Improving mapreduce performance through data placement in heterogeneous hadoop clusters. In Parallel & Distributed Processing, Workshops and Phd Forum (IPDPSW), 2010 IEEE International Symposium on (pp. 1-9). IEEE.

6. Zaharia, M., Konwinski, A., Joseph, A. D., Katz, R. H., & Stoica, I. (2008, December). Improving MapReduce Performance in Heterogeneous Environments. In OSDI (Vol. 8, No. 4, p. 7).

7. Jin, H., Yang, X., Sun, X. H., & Raicu, I. (2012, June). Adapt: Availability-aware mapreduce data placement for non-dedicated distributed computing. In Distributed Computing Systems (ICDCS), 2012 IEEE 32nd International Conference on (pp. 516-525). IEEE.

8. Perez, J. M., Garcia, F., Carretero, J., Calderon, A., & Sanchez, L. M. (2003, May). Data allocation and load balancing for heterogeneous cluster storage systems. In Cluster Computing and the Grid, 2003. Proceedings. CCGrid 2003. 3rd IEEE/ACM International Symposium on (pp. 718-723). IEEE.

Glossary
--------

* **Extent Store** - Persistent storage for the NDFS.

* **Guest VM** - A virtual machine hosted on a hypervisor that is serviced by
  the CVM.

* **Hypervisor**

* **iSCSI**

* **KVM**

* **NFS**

* **Oplog** - Persistent write buffer that is part of Stargate.

* **RF** - Replication factor. If the cluster is configured as RF(N), there are
  N copies of all pieces of data distributed across N nodes.

* **RPC** - Remote Process Call

* **VM** - Virtual Machine

Appendix
--------

TODO

[//]: # (Markdown cheatsheet: https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)

