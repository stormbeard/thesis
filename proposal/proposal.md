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
platform which proactively balances the file system workload based on node
capabilities can improve performance [5][6][7][8]. In this document, I propose
an adaptive data placement implementation for the Nutanix file system, aiming
to improve performance in heterogeneous clusters using the NDFS.

Distributed File Systems and Data Placement Overview
====================================================

### Hadoop Distributed File System (HDFS)

TODO [15]

### Ceph

TODO [16]

The Nutanix Distributed File System
===================================

The Nutanix Distributed File System (NDFS) is a distributed file system created
by Nutanix Inc., a San Jose based company [1]. The NDFS is facilitated by a
clustering of controller virtual machines (CVMs) which reside, one per node, on
each server in the cluster. The CVM presents via NFS, SMB, or iSCSI an
interface to each hypervisor that they reside on. For example, the interface
provided by the CVMs to VMware's ESXi hypervisor [14] will be interfaced with
as a datastore. The virtual machines' VMDK files will reside on the Nutanix
datastore and be accessed via NFS through the CVM sharing a host with the user
VM.

### Nutanix Cluster Components

Within the CVM lies an ecosystem of processes that work together to provide
NDFS services. Before I can explain the work proposed for this thesis, there
are two CVM processes that must be explained in more detail.

#### Cassandra (Distributed Metadata Store)

Cassandra stores and manager all cluster metadata in a distributed manner. The
version of Cassandra running in the NDFS is a heavily modified Apache
Cassandra. One of the main differences between Nutanix Cassandra and Apache
Cassandra is that Nutanix has implemented the Paxos algorithm to enforce strict
consistency.

#### Stargate (Data I/O Manager)

The Stargate process is responsible for all data management and I/O operations.
The NFS/SMB/iSCSI interface presented to the hypervisor is also presented by
Stargate. All file allocations and data replica placement decisions are also
made by this process.

As the Stargate process facilitates writes to disks, it gathers statistics for
each disk such as:

* The number of operations currently in flight on the disk (queue length)
* How much data in bytes currently resides on the disk
* Average time to complete an operation on the disk

Note that these statistics are only gathered on the local disks; however, they
are then stored in Cassandra along with the statistics gathered by every other
Stargate in the cluster. These disk statistics stored in Cassandra are pulled
periodically (currently every 30 seconds) and are then used to make decisions
on data placement when performing writes.

### Storage Tiering

Nutanix clusters are composed of servers that contain both SSDs and HDDs. These
disks obviously have a very large performance differential, so the NDFS has a
notion of storage tiers. Each storage tier contains similar groupings of disks
so that the NDFS can migrate "cold" or unused data from a tier containing fast
disks (such as SSDs or NVMe drives) down to a tier containing slower disks
(such as HDDs). This allows for optimizations in the file system such as
a persistent write buffer that only writes to SSDs and coalesces data to
before down-migrating to the HDDs via a single large, sequential write.
Stargate's data placement decisions are performed on a per-tier basis.

### Replica Disk Selection

When a write is made in the NDFS, data is written to multiple disks. The number
of data replicas is determined by a configurable setting called the Replication
Factor (RF). In an RF2 cluster, Stargate will attempt to place data on a local
disk and another copy of the data on a disk that resides on a remote node. This
will prevent data loss scenarios if a single node were to fail.

Currently, Stargate will attempt to select a number of disks corresponding to
the cluster RF that satisfy the following criteria:

* No two disks may reside on the same node.
* If there is a set of disks on the local node that can house a replica, choose one of those disks.

The disk selection logic is implemented via a random selection of all disks in
the storage tier. When a disk is selected, a node exclusion is asserted for
subsequent candidate disks so that we do not select two disks on the same node.

This selection methodology can be problematic for heterogeneous clusters since
it inherently assumes all disks in a specific tier are under similar load and
that each node can drive the same amount of writes to its disks.

Thesis Project Description
--------------------------

Motivation
==========

A number of scenarios arise in heterogeneous Nutanix clusters that can degrade
performance for an entire cluster. The currently replica disk selection logic
Stargate uses does not take into account a number of variables. For example,
there can be disparities in the following:

* Tier size
* CPU strength
* Running workload
* Disk health

Considering that a write is not complete until both copies (in an RF2 cluster)
are written, the write's performance is at the mercy of the slowest disk/node
combination. There are several scenarios, both pathological and daily
occurences, where a more robust replica placement heuristic is required.
To show the problems faced, I will focus on two orthogonal cases which many
other scenarios are a combination of.

### Interfering Workloads

Suppose we have a 3-node homogeneous cluster with only 2 nodes hosting active
workloads. In the current random selection scheme in use by the NDFS, writes
are equally likely to place their replica on the other node with an active
workload as they would be to place it on the idle node. This can impact
performance on both the local and remote workload. An adaptive replica
placement scheme would avoid the busy node and place its remote replica on the
idle node.

### Nodes with Severe Tier Disparities

Let's imagine we have a 3-node heterogeneous cluster with 2 high-end nodes and
a single weak node. Suppose these high-end nodes have 500GB of SSD tier and 6TB
of HDD tier and the single weak node has only 128GB of SSD tier and 1TB of HDD
tier. If 3 simultaneous workloads were to generate data such that the working
sets of the workloads are 50% of the local SSD tier, the weaker node is at a
great disadvantage. Given the current NDFS replica selection algorithm, we can
expect 500GB of replica traffic to flood the weak node and fill up its SSD tier
well before the workload is finished. An adaptive replica placement heuristic
would mitigate this issue by taking disk usages into consideration.

Adaptive Data Placement
=======================

To remedy the problems that arise from hetereogeneous cluster configurations
discussed in the previous section, I plan to implement an adaptive replica
placement algorithm for the Nutanix distributed file system. This algorithm
uses a "fitness value" that is calculated from various statistics available for
each disk such as disk fullness and queue depth. These fitness values are to be
used to rank each disk when selecting where the Stargate will place data. This
should mitigate many problems seen with heterogeneous Nutanix clusters.

### Fitness Values

A fitness value is a number calculated from the disk stats found in the NDFS
metadata store. During every NDFS disk stats update, new usage and performance
stats for each disk are pulled from the Cassandra database and stored in
Stargate memory at some periodic interval. For the work described in this
proposal, the stats used will be disk fullness percentage (fp) and disk queue
length (ql) in a function that defines fitness value as:

TODO: latex
```
  f = w1 * (fp / 100) ^ (1/2) + w2 * max(200 - ql, 0) / 200
```

The w1 and w2 variables are the weights for the disk fullness and queue length
terms respectively. These can be thought of as the maximum value allowed to be
contributed to the fitness value for each stat.

#### Metrics: Disk Queue Length

Disk queue length is the average number of Stargate operations in flight for
the duration of the last round of gathered statistics. A value of 200
operations was chosen as the ceiling, so if there anything higher than this
will not contribute to the fitness value. I've chosen to use this metric in the
fitness function due to the fact that it may be used across different types of
drive technologies without needing to change the default "worst-case" values
used when there is a failure gathering disk stats. If I were to use average
times for op completion, there would be a need to consider the type of drive
whose fitness is being measured. This metric combats the interfering workload
problem seen in both heterogeneous and homogeneous clusters.

#### Metrics: Disk Fullness

Disk fullness percentages are used in the fitness calculation so that disk
utilization remains mostly uniform as workloads generate data. Some
heterogeneous clusters include storage-heavy nodes with many large capacity
disks alongside nodes with low storage capcity. This metric combats the tier
disparity problem seen in heterogeneous clusters.

Since fitness values are used as weights during disk selection, an exponential
decay function was chosen for the disk fullness term because it provides a
property such that if two disks have some usage percentage differential, there
is a consistent relationship between the selection probabilities. For example,
the difference in selection probability for two disks that have a usage
percentage of 10% and 20% will be the same for two disks that have a usage
percentage of 50% and 60%.

### Weighted Random Selection Algorithms

Part of this work will be an exploration of various weighted random selection
algorithms that allow for a weighted "N choose 2" and an analysis of their
behavior and performance under various workloads and conditions. After a weight
is calculated for a disk in the cluster that will store a replica, we must
perform a weighted random selection on the set of potential candidate disks.
The schemes we will explore in this work are summarized in the next section.

Upon implementation of various selection algorithms, it will be necessary to
perform simulations of pathological cases in weighted random selection and
evaluate the chances of encountering these in day-to-day file system operations
and realistic workloads.

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
be as follows, suppose we have N objects (x_1, x_2, ..., x_n) in an array
(A) that represents the top T% of the total set. If we were to perform a
uniform random selection from this subset and yield x_2, I would simply swap
x_2 with the first element in the array x_1 and only consider the elements in
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
work of M.T. Chao [13] is omitted.

##### Algorithm R

Algorithm R was introduced by Vitter in 1985 [11] and runs in linear time
proportional to the number of elements in the set/stream. The algorithm can
sample k items as follows:

1. Select the first k items from the stream and insert into an array of size k.
2. For each item remaining in the stream j, such that j > k, choose a random integer M in [1, j].
3. If M <= k, replace item M of the array with item j.

Vitter showed that the probability of selecting an item after i iterations of
the algorithm is k/i. This is not directly useful for my investigation into
weighted random sampling; however, it is useful to give an overview of this
algorithm since Efraimidis and Spirakis [12] use a variation of AlgorithmR that
utilizes random sort and weights to accomplish a weighted-random variation of
reservoir sampling. This is explained in the next section.

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

### Weighted Random Selection Alternatives

I will also explore various ways to use the fitness values for very large sets
of disks. For example, when it's not feasible to perform a linear or
logarithmic selection from the set of disks, we can select some number of disks
that match our criteria and choose the disk with the largest fitness value.
This can be compared with the performance of the weighted sampling algorithms.

Testing and Benchmarks
======================

### Testing Replica Selection via Synthetic Workload Generation

To determine the viability of various fitness function parameters in different
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
manner. For this, I will use fio, a tool that will spawn a number of threads or
processes to generate I/O. This will allow for repeatability of various
workloads with specific read/write ratios, queue depths, run times, and working
sets. My tool will connect to each virtual machine simultaneously via SSH and
run the fio script corresponding to the desired workload.

After the fio scripts have finished running, the workload generation tool must
aggregate various performance statistics gathered by the fio processes running
on each virtual machine. This can then be analyzed at a later time after the
clusters are torn down.

Related Work
------------

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

TODO: C3 paper from FAST. This one is eerily similar to this proposal.

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

Preliminary Schedule
--------------------
| Task          | Time in Weeks |
| ------------- |:-------------:|
| CODE: Fio workload scripts | < 1 week |
| CODE: Workload VM deployment tool | 2 weeks |
| CODE: Workload data analysis scripts | 1 weeks |
| WRITE: Synthetic workload section of thesis | 2 weeks |
| MILESTONE: Workload generation complete | ----- |
| CODE: Fitness function framework for use with replica placement | 2 weeks |
| WRITE: NDFS fitness function implementation section of thesis | 2 week |
| CODE: Implement weighted random selection algorithms | 1 week |
| TEST/BENCHMARK: Weighted random pathological case unit test and evaluation | 1 week |
| WRITE: Weighted random and pathological case section of thesis | 1 week |
| CODE: Use disk usage and performance stats for placement decisions | < 1 week |
| TEST: Basic unit test simulations to sanity check fitness function | 1 week |
| MILESTONE: Adaptive data placement implementation complete | ----- |
| TEST: Add instrumentation to code base to troubleshoot odd behavior | < 1 week |
| WRITE: Unit test simulation and instrumentation section of thesis | 1 week |
| BENCHMARK: Generate workloads on multiple clusters and analyze the improvements | 2 weeks |
| MILESTONE: Testing and benchmarking on multiple clusters complete | ----- |
| WRITE: Benchmark results section of thesis (include analysis of algorithms) | 2 weeks |
| WRITE: Conclusions and future work | 1 week |
| WRITE: Introduction, Prior work | 2 weeks |
| WRITE: Nutanix file system overview | 1 week |
| WRITE: Finish thesis write-up | 2 weeks |
| THESIS APPROVAL | 4 weeks |

Approximate time to completion: 28 weeks

Bibliography
------------
 TODO: format the citations correctly

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

14. http://www.vmware.com/products/esxi-and-esx.html # TODO: fix this

15. Borthakur, D. (2008). HDFS architecture guide. HADOOP APACHE PROJECT http://hadoop. apache. org/common/docs/current/hdfs design. pdf, 39.

16. Weil, S. A., Brandt, S. A., Miller, E. L., Long, D. D., & Maltzahn, C.  (2006, November). Ceph: A scalable, high-performance distributed file system. In Proceedings of the 7th symposium on Operating systems design and implementation (pp. 307-320). USENIX Association.

Glossary
--------

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
