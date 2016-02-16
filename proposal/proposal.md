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

Introduction
------------

Remote Direct Memory Access (RDMA) is a standard in networked systems which
allows the memory of one computer (or node) to be accessed directly by another
node in the network, bypassing of their operating systems. This is especially
useful for clustered, latency-sensitive applications where there are many
nodes in constant communication over the network, such as a distributed
filesystem.

In this paper, I put forth a proposal to use RDMA for the RPCs sent between
the persistent write buffers of the Nutanix Distributed File System (NDFS).
The first part of this introduction will be a closer look at the NDFS, paying
close attention to the write path and the role of the persistent write buffers,
also known as the Oplog. The second half of this introduction will give an
overview of the current state of RDMA over Ethernet and the possible
improvements it can bring to network latencies.

### The Nutanix Distributed File System (NDFS)

TODO

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

Glossary
--------

* **RPC** - Remote Process Call

Appendix
--------

TODO

[//]: # (Markdown cheatsheet: https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)

