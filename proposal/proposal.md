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

Remote Direct Memory Access (RDMA) is a standard in networked systems which
allows the memory of one computer (or node) to be accessed directly by another
node in the network, bypassing both of the operating systems. This is especially
useful for clustered, latency-sensitive applications where there are many
nodes in constant communication over the network, such as a distributed
file system.

In this paper, I put forth a proposal to use RDMA for the RPCs sent between
the persistent write buffers of the Nutanix Distributed File System (NDFS).
The first part of this introduction will be a closer look at the NDFS core data
path, paying close attention to the write path and the role of the persistent
write buffers, also known as the Oplog. The second half of this introduction
will give an overview of the current state of RDMA over Ethernet and the
possible improvements it can bring to network latencies.

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

### Remote Direct Memory Access (RDMA)

As mentioned previously, RDMA is a set of mechanisms in networked systems which
allow the NIC to move data directly into and out of application buffers. This
allows the system to avoid copying memory from a user space application into
the kernel and from the kernel into NIC buffers. This direct access to memory
that bypasses the OS allows us to avoid the high overhead associated with the
movement of data.

#### The Cost of Data Movement

The desire to avoid data movement when communicating with distributed nodes is
born from work done by Clark et al. [4]. They found that even though TCP
overhead is comprised of a number of factors, it is mostly dominated by moving
data in memory is the largest contributor to transfer latency. Memory bandwidth
is the limiting factor when it comes to TCP processing.  In addition, Kay and
Pasquale found that the percentage of TCP overhead caused by data-touching
operations increases with packet size, since the time spent on per-byte
operations scales linearly with message size [5]. This shows that the highest
impact area of focus for communication latency reduction is copy avoidance.

#### Direct Data Placement (DDP) and RDMA

The DDP protocol is a means by which memory is exposed to a remote peer and
a means by which a peer may access the buffers designated by an upper layer
protocol, such as RDMA. While DDP provides a method of placing payloads into
specific buffers on a target, the RDMA protocol provides a method for
identification of these buffers to the application.

### RDMA Semantics

TODO

Project Description
-------------------

TODO

### Preliminary Analysis

Chu's 1996 paper on zero copy TCP in Solaris reported non-trivial per-byte
latency costs as a percentage of the total network software's costs:

| Packet Size | Percentage |
| 1500 byte Ethernet | 18-25% |
| 4352 byte FDDI | 35-50% |
| 9180 byte ATM | 55-65% |

During the writing of this proposal, I measured the size of Stargate Oplog RPCs
for both random and sequential write patterns to the NDFS. Below are graphs showing write size vs. RPC size for the different write patterns:

![random_write_rpc](images/original/random_write_rpc_size.png "RPC Sizes for Random Writes")

![sequential_write_rpc](images/original/sequential_write_rpc_size.png "RPC Sizes for Sequential Writes")

At the Stargate network layer, these RPCs would be broken up into multiple TCP
packets; however, with multiple 8kB RDDP buffers at the Stargate's disposal the
total RPC latency times would be reduced by at least 18% for 1500 byte MTU
packets.

Stargate RDMA Design and Architecture
-------------------------------------

Algorithms Used and Their Tradeoffs
-----------------------------------

TODO

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

