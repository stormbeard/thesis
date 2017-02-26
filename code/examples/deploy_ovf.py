#! /usr/bin/python
#
# Author: cyril0allen@gmail.com
#
# Deploy VMs to a freshly created nutanix cluster on ESX.

import os
import subprocess
import sys
from time import sleep

from vsphere_connector import VsphereConnector

vm_ova_filepath = "/home/tallen/thesis/vdb_0.ova"

class VCenterInfo:
  vcenter_ip              = "RTPVC6.rtp.nutanix.com"
  vcenter_username        = "rtp\\administrator"
  vcenter_password        = "nutanix/4u"
  vcenter_datacenter_name = "Tyrion-DC"
  vcenter_cluster_name    = "Tyrion-Cluster"

  def __init__(self):
    template = "{0:30}  {1:40}"
    print template.format("VCenter IP:",
                          self.vcenter_ip)
    print template.format("VCenter Username:",
                          self.vcenter_username)
    print template.format("VCenter Datacenter Name:",
                          self.vcenter_datacenter_name)
    print template.format("VCenter Cluster Name:",
                          self.vcenter_cluster_name)

# -----------------------------------------------------------------------------

def create_ctr(cvm_ip):
  default_ctr_name = run_cmd_on_cvm(cvm_ip, "ncli ctr ls | grep Name | head -1"
                                            "| grep default-container | "
                                            "cut -d\':\' -f2 |cut -d\' \' -f2")
  default_ctr_name = filter(lambda c: c != "\n", default_ctr_name)
  print "Default ctr name: " + default_ctr_name
  run_cmd_on_cvm(cvm_ip, "ncli ctr create name=%s ctr-name=%s" %
                         (default_ctr_name, default_ctr_name))
  run_cmd_on_cvm(cvm_ip, "ncli datastore create name=%s ctr-name=%s" %
                         (default_ctr_name , default_ctr_name))
  return default_ctr_name

# -----------------------------------------------------------------------------

def error_out(message):
  print "ERROR: " + message
  sys.exit(1)

# -----------------------------------------------------------------------------

def print_usage():
  print "Usage: ./deploy_ovf.py <CVM IP>"

# -----------------------------------------------------------------------------

# Sanity check the config in this script.
def validate(vc_info):
  # Make sure the ova exists.
  if not os.path.exists(vm_ova_filepath):
    error_out("No OVA found at location " + vm_ova_filepath)

  # Assert valid VCenter info.
  for field in filter(lambda x: not x.startswith("__"), dir(vc_info)):
    assert getattr(vcenter_info, str(field))

# -----------------------------------------------------------------------------

def run_cmd_on_cvm(cvm_ip, cmd):
  SSH_CMD = "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
  to_run = \
    ("sshpass -p nutanix/4u %s nutanix@%s \"source /etc/profile ; %s\"" %
    (SSH_CMD, cvm_ip, cmd))
  print "Running cmd: \n" + to_run
  output = os.popen(to_run).read()
  return output

# -----------------------------------------------------------------------------

# Single CVM IP to deduce host/cvm IPs from.
def determine_ips(cvm_ip):
  svmips_cmd = "svmips"
  hostips_cmd = "hostips"

  svmips = run_cmd_on_cvm(cvm_ip, svmips_cmd)
  if len(svmips) == 0:
    error_out("No SVM IPs found")
  else:
    print "Found svmips: " + str(svmips)

  hostips = run_cmd_on_cvm(cvm_ip, hostips_cmd)
  if len(hostips) == 0:
    error_out("No host IPs found")
  else:
    print "Found hostips: " + str(hostips)

  return hostips.split(), svmips.split()

# -----------------------------------------------------------------------------

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print_usage()
    sys.exit(1)

  vcenter_info = VCenterInfo()
  cvmip = sys.argv[1]

  print "Grabbing CVM and host IPs..."
  host_ips, cvm_ips = determine_ips(cvmip)

  print "Validating script input..."
  validate(vcenter_info)

  print "Connecting to vcenter..."
  vsc = VsphereConnector(vcenter_info.vcenter_ip,
                         vcenter_info.vcenter_username,
                         vcenter_info.vcenter_password)

  print "Reconnectin hosts to vcenter..."
  vsc.add_hosts(host_ips,
                vcenter_info.vcenter_datacenter_name,
                vcenter_info.vcenter_cluster_name)

  print "Create and mount the default container..."
  ctr_name = create_ctr(cvmip)

  print "Deploying UVMs to host group..."
  vm_objects = vsc.deploy_uvm_host_group(vm_ova_filepath,
                                         host_ips,
                                         ctr_name,
                                         vcenter_info.vcenter_datacenter_name,
                                         vcenter_info.vcenter_cluster_name)

  print "Booting VMs..."
  for vm in vm_objects:
    vsc.boot_vm(vm)


  retries=300
  vm_ips = map(lambda v: vsc.get_vm_ip(v), vm_objects)
  while None in vm_ips:
    print "UVM IPs: " + str(vm_ips)
    sleep(1)
    retries -= 1
    if (retries <= 0):
      print "Some VMs could not get an IP address."
      sys.exit(1)

  print "UVM IPs: " + str(vm_ips)

  print "Cleaning up."
  vsc.disconnect()
