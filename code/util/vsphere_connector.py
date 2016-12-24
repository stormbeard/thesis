# Author: tallen@nutanix.com
#
# Vsphere utility class for easy worker VM deployment automation.
#
# Some limitations:
#   -- All user/pass combos are hard-coded.

import errno
import logging
import os
import subprocess
import sys
import tarfile
import threading
import time

from pyVim import connect
from pyVmomi import vim

class VsphereConnector(object):
  """
  Wrapper class for PyVim various tasks.
  """

  def __init__(self, vcenter_ip, username, password):
    self.vcenter_ip = vcenter_ip
    self.vcenter_username = username
    self.vcenter_password = password
    self.service_instance = None
    self.logger = logging.getLogger()
    self.logger.setLevel(logging.DEBUG)

# -----------------------------------------------------------------------------

  @staticmethod
  def __str__():
    return "VsphereConnector"

# -----------------------------------------------------------------------------

  def si(self):
    if (self.service_instance == None):
      print "vcenter: " + self.vcenter_ip
      print "user: " + self.vcenter_username
      print "pwd: " + self.vcenter_password
      self.service_instance = connect.SmartConnect(
                                host=self.vcenter_ip,
                                user=self.vcenter_username,
                                pwd=self.vcenter_password,
                                port=443)
    return self.service_instance

# -----------------------------------------------------------------------------

  def content(self):
    return self.si().content

# -----------------------------------------------------------------------------

  def __get_obj(self, vimtype, name):
    """
    Get a pyvim object by its vimtype and name.
    """
    container = self.content().viewManager.CreateContainerView(
        self.content().rootFolder, vimtype, True)
    for obj in container.view:
      if obj.name == name:
        return obj
    return None

# -----------------------------------------------------------------------------

  def __get_cluster(self, cluster_name, dc_obj):
    """
    Finds a vim.ClusterComputeResource based on the name. Returns None if
    a cluster could not be found.
    """
    # TODO: Make this more efficient for huge vsphere clusters.
    clusters = dc_obj.hostFolder.childEntity
    for cluster in clusters:
      if cluster.name == cluster_name:
        return cluster
    return None

# -----------------------------------------------------------------------------

  def __get_resource_pool(self, cluster_obj):
    """
    Find the resource pool for a given cluster object.
    """
    resource_pool_object = cluster_obj.resourcePool
    return resource_pool_object

# -----------------------------------------------------------------------------

  def __get_datastore(self, datastore_name, datacenter_obj):
    """
    Returns datastore object if found and None otherwise.
    """
    # TODO: Make this more efficient for huge vsphere clusters.
    for ds_obj in datacenter_obj.datastoreFolder.childEntity:
      if ds_obj.name == datastore_name:
        return ds_obj
    return None

# -----------------------------------------------------------------------------

  def __get_datacenter(self, dc_name):
    """
    Find datacenter object.
    """
    # TODO: Make this more efficient for huge vsphere clusters.
    datacenter_object = self.__get_obj([vim.Datacenter], dc_name)
    if not datacenter_object:
      raise Exception("Invalid datacenter name (%s)." % dc_name)
    self.logger.debug("Found datacenter (%s)." % datacenter_object.name)
    return datacenter_object

# -----------------------------------------------------------------------------

  def __wait_for_task(self, task):
    """
    Blocks until a pyvmomi task is in the success or error state.
    """
    #TODO Add timeout.
    task_done = False
    while not task_done:
      try:
        if task.info.state == "success":
          return task.info.result
        if task.info.state == "error":
          task_done = True
      except:
        continue

# -----------------------------------------------------------------------------

  def __get_vm_by_name(self, vm_name, cluster):
    """
    Returns a VM object from within a specific ClusterComputeResource. If not
    found, None.
    """
    hosts = cluster.host
    for host in hosts:
      for vm in host.vm:
        if vm.name == vm_name:
          return vm
    return None

# -----------------------------------------------------------------------------

  def __get_host(self, host_name):
    """
    Find a host with the provided IP.
    """
    #TODO Make cluster-scope specific
    return self.__get_obj([vim.HostSystem], host_name)

# -----------------------------------------------------------------------------

  def __get_ovf_descriptor(self, ovf_location):
    """
    Gets the plain text OVF file data for the VM deployment.
    """
    f = open(ovf_location, 'r')
    ovfd = f.read()
    f.close()
    return ovfd

# -----------------------------------------------------------------------------

  def __extract_ova_data(self, ova_filepath):
    """
    Extracts OVA to .ovf and .vmdk files to ntnxiogen's cache of untarred OVA
    directories.

    Returns a dictionary containing the paths is returned.
    """
    # Check if we've already untarred the OVA. If yes, use that.
    ova_untar_dir = "/tmp/"
    assert(os.path.exists(ova_untar_dir))

    # Untar the OVA to extract the .ovf and .vmdk files from it.
    self.logger.warning("Untarring the OVA file {0}".format(ova_filepath))
    ova_tarball = tarfile.open(ova_filepath)
    ovf_and_vmdk = [ member for member in ova_tarball.getmembers() if
                     member.name.endswith(".vmdk") or
                     member.name.endswith(".ovf") ]
    self.logger.debug("OVF/VMDK {0}".format(ovf_and_vmdk))
    ova_tarball.extractall(ova_untar_dir, members=ovf_and_vmdk)
    ova_tarball.close()
    try:
      self.logger.warning("Untarred the OVA file {0}".format(ova_filepath))
    except OSError, ex:
      # Must have been racing with another task trying to untar this OVA.
      self.logger.warning("OVA file {0}".format(ova_filepath))

    return self.__build_ova_file_map(ova_filepath, ova_untar_dir)

# -----------------------------------------------------------------------------

  def __build_ova_file_map(self, ova_file_location, ova_untar_dir):
    """
    Return dict containing ovf and vmdk.
    """
    ova_tarball = tarfile.open(ova_file_location)
    ovf_and_vmdk = [ member for member in ova_tarball.getmembers() if
                     member.name.endswith(".vmdk") or
                     member.name.endswith(".ovf") ]
    ova_tarball.close()
    paths = map(lambda x: os.path.join(ova_untar_dir, x.name), ovf_and_vmdk)
    self.logger.debug("Paths for OVA extraction: {0}".format(paths))
    location_dict = {}
    for path in paths:
      if path.endswith(".vmdk"):
        self.logger.debug("Found VMDK path: %s" % path)
        if "vmdk" not in location_dict.keys():
          location_dict["vmdk"] = [path]
        else:
          location_dict["vmdk"].append(path)
      elif path.endswith(".ovf"):
        self.logger.debug("Found OVF path: %s" % path)
        location_dict["ovf"] = path
    return location_dict

# -----------------------------------------------------------------------------

  def __create_ovf_import_spec(self, ovf_descriptor, resource_pool, datastore):
    """
    Return the import spec for VM deployment.
    """
    #TODO Handle any OVF descriptor errors.  They fail silently and may
    # return None and fail further downstream.
    assert(resource_pool != None)
    assert(datastore != None)
    manager = self.content().ovfManager
    is_params = vim.OvfManager.CreateImportSpecParams(diskProvisioning="thin")
    import_spec = manager.CreateImportSpec(ovf_descriptor,
                                           resource_pool,
                                           datastore,
                                           is_params)
    assert(import_spec != None)
    return import_spec

# -----------------------------------------------------------------------------

  def __upload_vmdk(self, vmdk_path, target_url):
    self.logger.debug("POSTing %s to %s." % (vmdk_path, target_url))
    # Post the vmdk to host via curl.
    curl_cmd = ("curl -Ss -X POST --insecure -T %s -H 'Content-Type: "
                "application/x-vnd.vmware-streamVmdk' %s" %
                (vmdk_path, target_url))
    proc = subprocess.Popen(curl_cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            close_fds=True)
    stdout, stderr = proc.communicate()
    rv = proc.wait()
    if rv != 0:
      error_msg = "Failed to upload %s to %s: %d, %s, %s" % \
        (vmdk_path, target_url, rv, stdout, stderr)
      raise Exception

# -----------------------------------------------------------------------------

  def __deploy_virtual_appliance(self, lease, vmdk_paths):
    """
    Begins deployment of a vapp given the lease.
    """
    while (True):
      # If the lease is ready, begin deployment procedure.
      if (lease.state == vim.HttpNfcLease.State.ready):
        device_urls = lease.info.deviceUrl

        # Verify VMDK path count matches number of device URLs.
        if not (len(vmdk_paths) == len(device_urls)):
          self.logger.debug("VMDK file count does not match VMDK count in OVF "
                            "file.")
          raise Exception("Invalid OVA file contents. Cannot deploy VM.")

        for i in range(len(device_urls)):
          self._deployment_progress = int(float(i)/float(len(device_urls)))
          # Get correct VMDK file path for the URL.
          vmdk_path = vmdk_paths[i]
          target_url = device_urls[i].url.replace('*', self.vcenter_ip)
          upload_thread = threading.Thread(
              target=self.__upload_vmdk, args=(vmdk_path, target_url))
          upload_thread.start()
          threadAlive = True
          while(threadAlive):
            self.logger.debug("Thread is alive")
            lease.HttpNfcLeaseProgress(self._deployment_progress)
            self.logger.debug("Updating progress and attempting join")
            upload_thread.join(10)
            threadAlive = upload_thread.isAlive()
          self.logger.debug("Threads joined and moving to next vmdk")
        # Complete the lease and clean up the thread.
        self.logger.debug("Ready to release lease")
        lease.HttpNfcLeaseComplete()
        self.logger.debug("Lease released")
        return
      # If the lease errors out, log it and raise an exception.
      elif (lease.state == vim.HttpNfcLease.State.error):
        err_string = "Lease connection error (%s): %s" % (self.vcenter_ip,
                                                          lease.error.msg)
        self.logger.error(err_string)
        raise Exception("Lease connection error: %s" % lease.error.msg)

# -----------------------------------------------------------------------------

  def get_all_vms(self):
    """
    Provides a dictionary of all VM objects, indexed by name.
    """
    container = self.content().viewManager.CreateContainerView(
        self.content().rootFolder, [vim.VirtualMachine], True)
    vms = dict()
    for vm_obj in container.view:
      vms[vm_obj.name] = vm_obj
    return vms

# -----------------------------------------------------------------------------

  def wait_for_poweroff(self, vm):
    """
    Wait for a VM to fully power off before proceeding.
    """
    while True:
      try:
        if vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOff:
          return True
      except AttributeError:
        if vm == None:
          return False

# -----------------------------------------------------------------------------

  def get_vm_ip(self, vm):
    """
    Returns a VM objects IP address
    """
    return vm.summary.guest.ipAddress

# -----------------------------------------------------------------------------

  def clone_vm(self, vm_obj, new_name, dc_name, ds_name, host_ip, async=True):
    """
    Clones a VM object, returning a task if asynchronous.
    """
    # Get the appropriate objects.
    dc_obj = self.__get_datacenter(dc_name)
    assert(dc_obj != None)
    ds_obj = self.__get_datastore(ds_name, dc_obj)
    assert(ds_obj != None)
    host_obj = self.__get_host(host_ip)
    assert(host_obj != None)

    folder = dc_obj.vmFolder
    relospec = vim.vm.RelocateSpec()
    relospec.host = host_obj
    relospec.datastore = ds_obj
    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    task = vm_obj.Clone(folder=folder, name=new_name, spec=clonespec)
    if async:
      return task
    else:
      # TODO Ensure that the object returned is not an error state
      return self.__wait_for_task(task)

# -----------------------------------------------------------------------------

  def boot_vm(self, vm, async=True):
    """
    Boots a VM object, returning a task if asynchronous

    If the VM is already booted, the function will return None, but will not
    produce an error
    """
    #TODO Add timeout for synchronous task
    self.logger.warning("Attempting to boot {0}".format(vm.name))
    if vm.runtime.powerState == vim.VirtualMachine.PowerState.poweredOn:
      self.logger.warning("VM {0} is already powered on".format(vm.name))
      return None
    else:
      task = vm.PowerOn()
      if async:
        return task
      else:
        return self.__wait_for_task(task)

# -----------------------------------------------------------------------------

  def shutdown_vm(self, vm, async=True):
    """
    Shutsdown a VM, returning a task if asynchronous

    If the VM is already poweredOff, the function will return None and will not
    produce any errors
    """
    retry = True
    while retry:
      try:
        task = vm.ShutdownGuest()
        retry = False
      except vim.fault.ToolsUnavailable:
        self.logger.warning(
          "VM {0} doesn't have vm tools. Powering off".format(vm.name))
        task = vm.PowerOffVM()
      except vim.fault.TaskInProgress:
        self.logger.warning(
          "VM {0} is busy.  Retrying shutdown".format(vm.name))
        time.sleep(1)
      except vim.fault.InvalidState, vim.fault.InvalidPowerState:
        self.logger.warning("VM {0} is already powered off".format(vm.name))
        retry = False
      except Exception as e:
        self.logger.warning("Unknown exception raised: {0}".format(e.message))
    if async:
      return task
    else:
      self.wait_for_poweroff(vm)
      return

# -----------------------------------------------------------------------------

  def upload_file_vm(self, vm, filepath, remote_path):
    # TODO: This is somewhere in the community samples. Deal with it later.
    raise NotImplementedError

# -----------------------------------------------------------------------------

  def get_file_from_vm(self, vm, remote_path, local_path):
    """
    Retrieves a file on a guest and saves in a local directory
    """
    # TODO: This is somewhere in the community samples. Deal with it later.
    raise NotImplementedError

# -----------------------------------------------------------------------------

  def deploy_uvm_host_group(self,
                            ova_filepath,
                            host_ip_list,
                            datastore_name,
                            datacenter_name,
                            cluster_name):
    """
    Deploy OVA to each host in the 'host_ip_list'. This is done via a
    deployment of a template VM that is cloned to each host.
    """
    # TODO: remove the template when finished.

    assert(len(host_ip_list) > 0)

    # Remove any duplicates
    host_ip_list = list(set(host_ip_list))

    # Deploy to the first host in the list.
    template = self.deploy_uvm(ova_filepath,
                               host_ip_list[0],
                               datastore_name,
                               datacenter_name,
                               cluster_name)

    # Clone the VMs off the deployed template.
    task_list = []
    clone_vm_name_list = []
    for host in host_ip_list:
      new_vm_name = template.name + "-" + str(len(task_list))
      task_list.append(
        self.clone_vm(
          template, new_vm_name, datacenter_name, datastore_name, host))
      clone_vm_name_list.append(new_vm_name)
    for t in task_list:
      self.__wait_for_task(t)

    # Return a list of the VM objects we deployed.
    vm_obj_list = []
    dc_obj = self.__get_datacenter(datacenter_name)
    cluster_obj = self.__get_cluster(cluster_name, dc_obj)
    for name in clone_vm_name_list:
      vm_obj_list.append(self.__get_vm_by_name(name, cluster_obj))

    return vm_obj_list

# -----------------------------------------------------------------------------

  def deploy_uvm(self,
                 ova_filepath,
                 host_ip,
                 datastore_name,
                 datacenter_name,
                 cluster_name):
    """
    Deploy a single copy of a VM specified by the on the host specified by
    host_ip. This call fails if the VM already exists.

    Returns the VM.
    """
    file_location_map = self.__extract_ova_data(ova_filepath)
    vmdk_paths = file_location_map["vmdk"]
    ovf_path = file_location_map["ovf"]
    ovfd = self.__get_ovf_descriptor(ovf_path)

    # Get all the required objects.
    datacenter_obj = self.__get_datacenter(datacenter_name)
    assert(datacenter_obj != None)
    cluster_obj = self.__get_cluster(cluster_name, datacenter_obj)
    assert(cluster_obj != None)
    resource_pool = self.__get_resource_pool(cluster_obj)
    assert(resource_pool != None)
    datastore_obj = self.__get_datastore(datastore_name, datacenter_obj)
    assert(datastore_obj != None)
    import_spec = self.__create_ovf_import_spec(
      ovfd, resource_pool, datastore_obj)
    self.logger.debug("Import Spec {0}".format(import_spec))
    vm_folder = datacenter_obj.vmFolder
    for host in cluster_obj.host:
      if (host.name == host_ip):
        host_obj = host
        break

    # Import the virtual appliance.
    lease = resource_pool.ImportVApp(
      import_spec.importSpec, folder=vm_folder, host=host_obj)
    self.__deploy_virtual_appliance(lease, vmdk_paths)

    return lease.info.entity

# -----------------------------------------------------------------------------

  def __get_unknown_host_thumbprint(self, host_ip, root_password):
    """
    For hosts that aren't part of the vcenter yet, we need to connect directly
    and pull their SSL thumbprint information to connect them painlessly.
    """
    # TODO: Use paramiko so we don't rely on sshpass.
    fingerprint_cmd = \
      "sshpass -p \'" + root_password + \
      "\' ssh -o StrictHostKeyChecking=no root@" + host_ip + \
      " \"openssl x509 -in /etc/vmware/ssl/rui.crt -fingerprint -sha1 " + \
      "-noout\""
    fingerprint_output = os.popen(fingerprint_cmd).read()
    if not "Fingerprint" in fingerprint_output:
      sys.exit()
    else:
      thumbprint = fingerprint_output.split("=")[1]
      # Strip the newline from end.
      return thumbprint[:-1]

# -----------------------------------------------------------------------------

  def add_hosts(self,
                host_names,
                dc_name,
                cluster_name,
                root_password="nutanix/4u"):
    """
    Given a list of host names (typically the host IPs), the hosts will be
    added to the specified datacenter and cluster.
    """
    # Remove duplicate hosts.
    host_names = list(set(host_names))
    dc_obj = self.__get_datacenter(dc_name)
    if (dc_obj == None):
      raise Exception("Datacenter %s not found." % dc_name)
    cluster_obj = self.__get_cluster(cluster_name, dc_obj)
    if (cluster_obj == None):
      raise Exception("Cluster %s not found." % cluster_name)

    # TODO: Parallelize this via task list or CommandExecutor.
    task_list = []
    for hn in host_names:
      host_obj = self.__get_host(hn)
      connect_spec = vim.host.ConnectSpec()
      connect_spec.force = True
      connect_spec.userName = "root"
      connect_spec.password = root_password
      connect_spec.hostName = hn
      if (host_obj == None):
        connect_spec.sslThumbprint = \
          self.__get_unknown_host_thumbprint(hn, root_password)
      else:
        connect_spec.sslThumbprint = host_obj.summary.config.sslThumbprint
      # Remove the host if already in cluster and re-add.
      if host_obj in cluster_obj.host:
        self.__wait_for_task(host_obj.Destroy())
      task_list.append(
        cluster_obj.AddHost_Task(spec=connect_spec, asConnected=True))

    for t in task_list:
      self.__wait_for_task(t)
