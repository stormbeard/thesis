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

TODO: Heterogeneous cluster use-cases and problems that arise.
* Aging clusters and expansion over time. Different generations of nodes.
* Mixing all-flash with hybrid HDD/SSD nodes.
* Mixing in storage-only nodes with heavy HDD

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

TODO: This is already in place and not part of the proposed thesis project.

### Selection Algorithms

Part of this work will be an exploration of various weighted random selection
algorithms and an analysis of their behavior and performance under various
workloads and conditions. After a weight is calculated for a disk in the
cluster that will store a replica, we must perform a weighted random selection
on the set of potential candidate disks. The schemes we will explore in this
work are summarized below.

#### Trucation Selection

Trucation selection was first introduced by Muhlenbein and Schlierkamp-Voosen
in 1993 as part of their work on Breeder Genetic Algorithms [9]. The basic idea
is that there is a threshold percentage (T) that will indicate the top T% most
fit elements in a set. From this top T%, individuals are selected and mated
randomly until the number of offspring can replace the parent population.

For the purposes of the work in this proposal, I have no need for the breeding
aspect of Muhlenbein and Schlierkamp-Voosen's work. I will simply stop at the
uniform random selection of individuals from the top T% elements in the set of
disks. To avoid selecting the same disk from the set multiple times, it will be
required that an exclusion scheme be employed. The way I will handle this is to
simply remove the object from the sampling set if it is determined unsuitable
for the purposes we're performing selection for. A more concrete example would
be as follows, suppose we have N objects (x~1~, x~2~, ..., x~n~) in an array
(A) that represents the top T% of the total set. If we were to perform a
uniform random selection from this subset and yield x~2~, I would simply swap
x~2~ with the first element in the array x~1~ and only consider the elements in
A[1:]. This scheme is worst-case O(N) and guarantees that some fixed percentage
of the weaker candidates will not be selected.

#### Stochastic Universal Sampling (SUS)

SUS is another sampling technique first introduced by Baker in 1987 [10]. The
algorithm can be understood as follows:

On a standard roulette wheel there's a single pointer that indicates the
winner. The roulette wheel's "bins" can all be the same size which would
indicate a uniform probability of selecting any bin and could also be unevenly
sized which would indicate a weighted probability. SUS uses this same concept
except allows for N evenly spaced pointers corresponding to the selection of N
items. Key things to note are that the set, or "bins" in my roulette
analogy, must be shuffled prior to selection and there is a minimum spacing
allowed for the pointers to prevent selection of the same bin by two pointers.

#### Reservoir Sampling

Reservoir sampling describes an entire family of stochastic algorithms for
randomly sampling items from a very large set. Typically, the number of
elements in the set is so large that it cannot fit into main memory. This
summary will only focus on non-distributed reservoir sampling; therefore, the
work of M.T. Chao [13] is ommitted.

##### Algorithm R

Algorithm R was introduced by Vitter in 1985 [11] and runs in linear time
proportional to the number of elements in the set/stream. The algorithm can
sample k items as follows:

1. Select the first k items from the stream and insert into an array of size k.
2. For each item remaining in the stream j, such that j > k, choose a random integer M in [1, j].
3. If M <= k, replace item M of the array with item j.

Vitter showed that the probability of selecting an item after i iterations of
the algorithm is k/i. This is not directly useful for my investigation into
weighted random sampling; however, Efraimidis and Spirakis [12] use a variation of
this that utilizes random sort and weights to accomplish a weighted-random
variation of reservoir sampling. This is explained in the next section.

##### Weighted Random Sampling via Reservoir

This algorithm performs a weighted random selection via the use of a priority
queue data structure. To sample k elements from a set/stream, the algorithm
is summarized using the following pseudocode:
```
While the stream has data:
  r = InclusiveRandom(0,1) ** (1 / element_weight)
  if p_queue.Size() < k:
    p_queue.Insert(r, element)
  else:
    p_queue.PopMin()
    p_queue.Insert(r, element)
```

Efraimidis and Spirakis proved that the resulting priority queue will contain a
set of k elements whose probability of being included with the set is
proportional to their weights.

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

1. Poitras, S. (2015, November 11). The Nutanix Bible - NutanixBible.com. Retrieved February 15, 2016, from http://nutanixbible.com/

2.  Lakshman, A., & Malik, P. (2008, August 25). Cassandra – A structured storage system on a P2P Network. Retrieved February 15, 2016, from https://www.facebook.com/notes/facebook-engineering/cassandra-a-structured-storage-system-on-a-p2p-network/24413138919/

3. Dean, J., & Ghemawat, S. (2008). MapReduce: simplified data processing on large clusters. Communications of the ACM, 51(1), 107-113.

4. hadoop.apache.org # TODO: fix this

5. Xie, J., Yin, S., Ruan, X., Ding, Z., Tian, Y., Majors, J., ... & Qin, X. (2010, April). Improving mapreduce performance through data placement in heterogeneous hadoop clusters. In Parallel & Distributed Processing, Workshops and Phd Forum (IPDPSW), 2010 IEEE International Symposium on (pp. 1-9). IEEE.

6. Zaharia, M., Konwinski, A., Joseph, A. D., Katz, R. H., & Stoica, I. (2008, December). Improving MapReduce Performance in Heterogeneous Environments. In OSDI (Vol. 8, No. 4, p. 7).

7. Jin, H., Yang, X., Sun, X. H., & Raicu, I. (2012, June). Adapt: Availability-aware mapreduce data placement for non-dedicated distributed computing. In Distributed Computing Systems (ICDCS), 2012 IEEE 32nd International Conference on (pp. 516-525). IEEE.

8. Perez, J. M., Garcia, F., Carretero, J., Calderon, A., & Sanchez, L. M. (2003, May). Data allocation and load balancing for heterogeneous cluster storage systems. In Cluster Computing and the Grid, 2003. Proceedings. CCGrid 2003. 3rd IEEE/ACM International Symposium on (pp. 718-723). IEEE.

9. Schlierkamp-Voosen, D., & Mühlenbein, H. (1993). Predictive models for the breeder genetic algorithm. Evolutionary Computation, 1(1), 25-49.

10. Baker, J. E. (1987, July). Reducing bias and inefficiency in the selection algorithm. In Proceedings of the second international conference on genetic algorithms (pp. 14-21).

11. Vitter, J. S. (1985). Random sampling with a reservoir. ACM Transactions on Mathematical Software (TOMS), 11(1), 37-57.

12. Efraimidis, P. S., & Spirakis, P. G. (2006). Weighted random sampling with a reservoir. Information Processing Letters, 97(5), 181-185.

13. Chao, M. T. (1982). A general purpose unequal probability sampling plan.  Biometrika, 69(3), 653-656.

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

