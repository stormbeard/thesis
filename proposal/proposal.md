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

#### The Nutanix Solution

Nutanix is a software company headquartered in San Jose, CA. The bundled
hardware/software solution sold by Nutanix consists at least 3 servers that run
an industry standard hypervisor (VMware ESXi, Microsoft Hyper-V, or Linux KVM).
Storage I/O for the guests hosted on the hypervisor is sent to the Nutanix
Controller VM (CVM) to be serviced [1]. The figure below shows what a single
node in a Nutanix cluster typically looks like:

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
only process on the CVM that direclty manipulates data on disk.

TODO: life of a write, replications

### Remote Direct Memory Access (RDMA)

TODO

Project Description
-------------------

TODO

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

1. Poitras, S. (2015, November 11). The Nutanix Bible - NutanixBible.com.
Retrieved February 15, 2016, from http://nutanixbible.com/

2.  Lakshman, A., & Malik, P. (2008, August 25). Cassandra – A structured storage system on a P2P Network. Retrieved February 15, 2016, from https://www.facebook.com/notes/facebook-engineering/cassandra-a-structured-storage-system-on-a-p2p-network/24413138919/ 

Glossary
--------

* **ESXi** - The hypervisor created by VMware.

* **Guest VM** - A virtual machine hosted on a hypervisor that is serviced by
  the CVM.

* **Hyper-V**

* **Hypervisor**

* **iSCSI**

* **KVM**

* **NFS**

* **Oplog**

* **RF** - Replication factor. If the cluster is configured as RF(N), there are
  N copies of all pieces of data distributed across N nodes.

* **RPC** - Remote Process Call

* **SMB**

* **VM** - Virtual Machine

Appendix
--------

TODO

[//]: # (Markdown cheatsheet: https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)

