### Proposal for a Thesis in the Field of Information Technology
#### For Partial Fulfillment of Requirements For a Master of Liberal Arts Degree

#### Harvard University Extension School
#### Submission Date

#### Cyril Allen
500 N. Duke St.

Apt. 55-305

Durham, NC 27701

[cyril0allen@gmail.com](mailto:cyril0allen@gmail.com)

Abstract
--------

TODO

Introduction
------------

TODO

### Nutanix

Nutanix is a software company headquartered in San Jose, CA. The bundled
hardware/software solution sold by Nutanix consists of at least 3 servers that
run an industry standard hypervisor (VMware ESXi, Microsoft Hyper-V, or Linux
KVM).  Storage I/O for the guests hosted on the hypervisor is sent to the
Nutanix Controller VM (CVM) to be serviced [1]. The figure below shows what a
single node in a Nutanix cluster logically looks like:

![nutanix_solution](images/1/converged_platform.png "The Nutanix Solution")

The CVM is networked together with the CVMs from other servers and creates a
distributed system that manages all storage resources. Each CVM exports block
devices that appear as disks to the guest VMs that utilize the NDFS. All data
that is written to the block device presented by Nutanix is replicated across 2
nodes for a replication factor (RF) 2 configuration and 3 nodes for a RF3
configuration.

#### The Nutanix CVM

The CVM runs a CentOS 6.5 operating system and the services it provides are
accessed by the hypervisor remotely via NFS, SMB, or iSCSI for the ESXi,
Hyper-V, or KVM hypervisors respectively. The process that provides the
interface to the hypervisors to enable I/O service is known as the Stargate
process.

#### Stargate

Stargate is responsible for all data management and I/O operations and is the
only process on the CVM that directly manipulates data on disk. The Stargate
process is comprised of several components, but the ones relevant for this
proposal are the Oplog and the Extent Store. The Oplog acts as a write buffer
to absorb random I/O and the Extent Store can be thought of as the persistent
data storage. This document proposes a project that directly deals with the
Oplog, so in the next section we'll dive deeper into that component.

##### The Oplog

The Oplog is a persistent write buffer for Stargate and serves to decrease write
latency by absorbing bursts of random writes. All writes that are absorbed by
the Oplog are written directly to SSD and synchronously replicated to other CVMs
in the cluster to satisfy the replication factor requirements as configured by
the NDFS user before the write is acknowledged. These writes are also coalesced
if possible, further increasing performance by reducing CPU utilization of
handling multiple nearby writes.

Data in Oplog is "drained" to the Extent store in the background to make room
for more random writes. For sequential workloads, the Oplog is bypassed and the
writes go straight into the Extent Store. All reads that need data residing
in the Oplog will have that data serviced directly by the Oplog until it drains.

##### The Extent Store

TODO

#### The Current State of Replica Selection

TODO: Explain rack awareness

### The Current issues with Heterogeneous Clusters

TODO: 
-- Inconsistent space utilization on nodes.
-- Overburdening small nodes via replica traffic

### Nutanix Cluster Hardware Configurations

TODO: Describe RUs, nodes, networking, and anything else infrastructure-wise

Project: Adaptive Replica Selection
-------------------

TODO: Describe the overall plan of assigning a fitness function to each disk
and ranking them for selection. Possible Rackable unit and node-level fitness
to be used as well.

Also mention there will be benchmarks and tests.

### Fitness Score Calculation

TODO: Mention the stats available to us and how they'll be used in the
calculations for each level.

#### Fitness Score Hierarchies

TODO: Explain the model

##### Disk-level Fitness

TODO: The function that'll be used.

##### Node-level Fitness

TODO: The method of calculation given the disk-level stats. How will we handle
the disk-level variance? Is median disk fitness a good metric?

##### RU-level Fitness

TODO: The method of calculation given the disk and node-level stats. Same
issues as above but disk AND node.

### Ranking Algorithm

TODO: Mention priority queue.

#### The ReplicaQueue Class

TODO: Its interface and the WeightedSample() function's magic. Also mention
it's rebuilt on ZeusConfigChangeNotification().

#### Weighted Shuffling

TODO: "Prettiest girl at the bar" problem and approaches to fixing it.

-- AlarmHandler and ZeusConfigChangeNotification reshuffling.
-- Providing access to the weight vector from ReplicaQueue to do individual
   sampling in O(N).

### Polling for Remote Disk Stats

TODO: The problem, where the data is stored, and how we're getting it.

### ReplicaSelector Changes

TODO: ReplicaSelector is modified so that both the Extent Store an Oplog will
benefit from the adaptive selection.

Also mention the "big cluster-wide" vector approach and the RU -> node -> disk
approach.

Testing and Benchmarks
----------------------

### Unit Testing Replica Selection via Simulation

TODO: Explain the current unit tests and various scenarios.

### Testing Replica Selection via Synthetic Workload Generation

TODO: Explain that we have X-ray and we want to compare the results.

Related Work
------------

TODO

Hardware Requirements
---------------------

TODO

Software Requirements
---------------------

TODO

Benchmarks and Performance Analysis Methodology
-----------------------------------------------

TODO

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

3. TODO: Romanow paper

4. D. D. Clark, V. Jacobson, J. Romkey, H. Salwen, "An analysis if TCP processing protocols", Proceedings of the ACM SIGCOMM Conference 1990

5. J. Kay, J. Pasquale, "Profiling and reducing processing overheads in TCP/IP", IEEE/ACM Transactions on Networking, Vol. 4, No. 6, pp.817-828, December 1996

6. H. K. Chu, "Zero-copy TCP in Solaris", Proc. of the USENIX 1996 Annual Technical Conference, San Diego, CA, January 1996

Glossary
--------

* **ATM**

* **ESXi** - The hypervisor created by VMware.

* **Extent Store** - Persistent storage for the NDFS.

* **FDDI

* **Guest VM** - A virtual machine hosted on a hypervisor that is serviced by
  the CVM.

* **Hyper-V**

* **Hypervisor**

* **iSCSI**

* **KVM**

* **MTU**

* **NFS**

* **NIC** - Network interface card.

* **Oplog** - Persistent write buffer that is part of Stargate.

* **RF** - Replication factor. If the cluster is configured as RF(N), there are
  N copies of all pieces of data distributed across N nodes.

* **RPC** - Remote Process Call

* **SMB**

* **VM** - Virtual Machine

Appendix
--------

TODO

[//]: # (Markdown cheatsheet: https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)

