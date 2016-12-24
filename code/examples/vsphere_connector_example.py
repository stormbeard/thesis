# Author: Tony Allen (cyril0allen@gmail.com)
#
# In its current state, this script does nothing and is a total hack using
# various automation I wrote for day-to-day Nutanix stuff. It's SUPPOSED to
# deploy worker VMs to a freshly created Nutanix cluster.

import os
import subprocess
import sys
from time import sleep

# Probably doesn't work as-is.
from vsphere_connector import VsphereConnector

# Break out of this early until I can test.
sys.exit(0)

vcenter_ip        = # TODO
vcenter_username  = # TODO
vcenter_password  = # TODO
vcenter_datacenter_name = "tony_test_dc"
vcenter_cluster_name    = "tony_test_cluster"
vcenter_datastore_name = "tony_test_ds"

worker_vm_ova_filepath = # TODO

# Single CVM IP to deduce host/cvm IPs from.
def determine_ips(cvm_ip, nutanix_pass="nutanix/4u"):
  svmips_cmd = "sshpass -p " + nutanix_pass + " ssh nutanix@" + cvm_ip + \
    " \"source /etc/profile; svmips\""
  hostips_cmd = "sshpass -p nutanix/4u ssh nutanix@" + cvm_ip + \
    " \"source /etc/profile; hostips\""
  svmips = os.popen(svmips_cmd).read()
  hostips = os.popen(hostips_cmd).read()
  return hostips.split(), svmips.split()

host_ips, cvm_ips = determine_ips(sys.argv[1])
print "host: " + str(host_ips)
print "cvm: " + str(cvm_ips)

# Connect to vcenter.
vsc = VsphereConnector(vcenter_ip, vcenter_username, vcenter_password)

# Reconnect hosts to vcenter.
vsc.add_hosts(host_ips, vcenter_datacenter_name, vcenter_cluster_name)

# Deploy VM to all hosts.
vm_objects = vsc.deploy_uvm_host_group(worker_vm_ova_filepath,
                                       host_ips,
                                       vcenter_datastore_name,
                                       vcenter_datacenter_name,
                                       vcenter_cluster_name)

# Boot all the deployed VMs.
for vm in vm_objects:
  vsc.boot_vm(vm)

# Wait for them all to get IPs. I'm choosing to wait 5 mins.
retries=300
while None in map(lambda v: vsc.get_vm_ip(v), vm_objects):
  sleep(1)
  retries -= 1
  if (retries <= 0):
    raise Exception("Some VMs could not get an IP address.")

print "UVM IPs: " + str(map(lambda v: vsc.get_vm_ip(v), vm_objects))
