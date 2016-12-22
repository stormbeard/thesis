#!/usr/bin/env python
#
# Copyright (c) 2015 Nutanix Inc. All rights reserved.
#
# Author: gasmith@nutanix.com
#
# A simple script for backing up and restoring VMs from acropolis.
#
# In backup mode (--action=backup), this script copies the VM descriptor and
# disks (identified by --vm_name) from a specified Nutanix cluster
# (--cluster_ip) to a path of your choice (--backup_path).
#
# In restore mode (--action=restore), this script restores the backup data
# (--backup_path) to a Nutanix cluster (--cluster_ip) in a container of your
# choice (--restore_container).
#
# Prerequisites:
#  - The host that runs this script must have autofs /net enabled.
#  - The host that runs this script must be added to the cluster's NFS
#    whitelist.
#

import errno
import gflags
import json
import os
import requests
import shutil
import subprocess
import traceback
import urllib
import uuid

gflags.DEFINE_string("action", None,
                     "Action ('backup' or 'restore')")

gflags.DEFINE_string("cluster_ip", None,
                     "Cluster IP address (CVM or virtual IP)")

gflags.DEFINE_string("username", "admin", "Prism username")

gflags.DEFINE_string("password", "admin", "Prism password")

gflags.DEFINE_string("vm_name", None, "VM name")

gflags.DEFINE_string("backup_path", None, "Backup location")

gflags.DEFINE_string("restore_container", "default", "Container for restore")

gflags.DEFINE_string("restore_network_uuid", None, "Network UUID for restore")

gflags.DEFINE_boolean("keep_mac_addresses", True,
                      "Whether to retain mac addresses")

gflags.DEFINE_boolean("compress_disks", True,
                      "Whether to compress virtual disks (requires qemu-img)")

FLAGS = gflags.FLAGS

class RestApiClient():

  def __init__(self, cluster_ip, username, password):
    """
    Initializes the options and the logfile from GFLAGS.
    """
    self.cluster_ip = cluster_ip
    self.username = username
    self.password = password
    self.base_acro_url = (
        "https://%s:9440/api/nutanix/v0.8" % (self.cluster_ip,))
    self.base_pg_url = (
        "https://%s:9440/PrismGateway/services/rest/v1" % (self.cluster_ip,))
    self.session = self.get_server_session(self.username, self.password)

  def get_server_session(self, username, password):
    """
    Creating REST client session for server connection, after globally setting
    Authorization, Content-Type and charset for session.
    """
    session = requests.Session()
    session.auth = (username, password)
    session.verify = False
    session.headers.update(
        {'Content-Type': 'application/json; charset=utf-8'})
    return session

  def _url(self, base, path, params):
    """
    Helper method to generate a URL from a base, relative path, and dictionary
    of query parameters.
    """
    if params:
      return "%s/%s?%s" % (base, path, urllib.urlencode(params))
    else:
      return "%s/%s" % (base, path)

  def acro_url(self, path, **params):
    """
    Helper method to generate an Acropolis interface URL.
    """
    return self._url(self.base_acro_url, path, params)

  def pg_url(self, path, **params):
    """
    Helper method to generate an Prism Gateway interface URL.
    """
    return self._url(self.base_pg_url, path, params)

  def resolve_vm_uuid(self, vm_name):
    """
    Resolves a VM name to a UUID. Fails if the name is not found, or not
    unique.
    """
    # Use prism gateway interface to do a filtered query.
    url = self.pg_url("vms", filterCriteria="vm_name==" + vm_name)
    r = self.session.get(url)
    if r.status_code != requests.codes.ok:
      raise Exception("GET %s: %s" % (url, r.status_code))

    # Make sure we got one unique result.
    obj = r.json()
    count = obj["metadata"]["count"]
    if count == 0:
      raise Exception("Failed to find VM named %r" % (vm_name,))
    if count > 1:
      raise Exception("VM name %r is not unique" % (vm_name,))

    # Prism likes to prepend the VM UUID with a cluster ID, delimited by "::".
    parts = obj["entities"][0]["vmId"].rsplit(":", 1)
    return parts[-1]

  def get_vm_info(self, vm_uuid):
    """
    Fetches the VM descriptor.
    """
    # Use acropolis interface to fetch the vm configuration.
    url = self.acro_url("vms/%s" % (vm_uuid,))
    r = self.session.get(url)
    if r.status_code != requests.codes.ok:
      raise Exception("GET %s: %s" % (url, r.status_code))
    return r.json()

  def get_snapshot_info(self, snap_uuid):
    """
    Fetches the snapshot descriptor.
    """
    # Use acropolis interface to fetch the snapshot configuration.
    url = self.acro_url("snapshots/%s" % (snap_uuid,))
    r = self.session.get(url)
    if r.status_code != requests.codes.ok:
      raise Exception("GET %s: %s" % (url, r.status_code))
    return r.json()

  def create_snapshot(self, vm_uuid, snap_uuid):
    """
    Creates a temporary snapshot of the VM.
    """
    print("Creating temporary snapshot %s for VM %s" % (snap_uuid, vm_uuid))
    url = self.acro_url("snapshots")
    payload = {
      "snapshotSpecs": [{
        "uuid": snap_uuid,
        "vmUuid": vm_uuid,
      }]
    }
    r = self.session.post(url, data=json.dumps(payload))
    if r.status_code != requests.codes.ok:
      raise Exception("POST %s: %s" % (url, r.status_code))

    task_uuid = r.json()["taskUuid"]
    self.poll_task(task_uuid)

  def delete_snapshot(self, snap_uuid):
    """
    Deletes the specified snapshot.
    """
    print("Deleting temporary snapshot %s" % (snap_uuid,))
    url = self.acro_url("snapshots/%s" % (snap_uuid,))
    self.session.delete(url)

  def get_container_name(self, ctr_id):
    """
    Resolves a container ID to a container name.
    """
    url = self.pg_url("containers/%s" % (ctr_id,))
    r = self.session.get(url)
    if r.status_code != requests.codes.ok:
      raise Exception("GET %s: %s" % (url, r.status_code))
    obj = r.json()
    return obj["name"]

  def poll_task(self, task_uuid):
    """
    Polls a task until it completes. Fails if the task completes with an error.
    """
    url = self.acro_url("tasks/%s/poll" % (task_uuid,))
    while True:
      print("Polling task %s for completion" % (task_uuid,))
      r = self.session.get(url)
      if r.status_code != requests.codes.ok:
        raise Exception("GET %s: %s" % (url, r.status_code))

      task_info = r.json().get("taskInfo")
      if task_info is None:
        continue
      mr = task_info.get("metaResponse")
      if mr is None:
        continue
      if mr["error"] == "kNoError":
        break
      else:
        raise Exception("Task %s failed: %s: %s" %
            (task_uuid, mr["error"], mr["errorDetail"]))

  def create_backup(self, backup_path, snap_info, vm_info):
    """
    Creates a backup of the VM in the specified directory, by copying out each
    non-trivial disk over NFS and writing a serialized VM descriptor.
    """
    # Create the backup directory if it doesn't exist.
    try:
      os.makedirs(backup_path)
    except OSError as ex:
      if ex.errno != errno.EEXIST:
        raise

    # Write out the VM descriptor as a JSON file.
    print("Writing VM descriptor file")
    vm_info_file = os.path.join(backup_path, "vm.json")
    with open(vm_info_file, "w") as fobj:
      json.dump(vm_info, fobj)

    # Copy the disk content from the snapshotted disks.
    group_uuid = snap_info["groupUuid"]
    for disk in vm_info["config"]["vmDisks"]:
      if not disk["isEmpty"]:
        print("Copying data for disk %s" % (disk["id"],))
        vmdisk_uuid = disk["vmDiskUuid"]
        ctr_id = disk["containerId"]
        ctr_name = self.get_container_name(ctr_id)
        src_path = (
            "/net/%s/%s/.acropolis/snapshot/%s/vmdisk/%s" %
            (self.cluster_ip, ctr_name, group_uuid, vmdisk_uuid))
        if FLAGS.compress_disks and not disk["isCdrom"]:
          dst_path = "%s/%s.qcow2" % (backup_path, vmdisk_uuid)
          proc = subprocess.Popen([
            "qemu-img", "convert", "-c", "-O", "qcow2", src_path, dst_path ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
          stdout, stderr = proc.communicate()
          ret = proc.returncode
          if ret != 0:
            raise Exception(
                "Failed to compress image (%d): %s %s" % (ret, stdout, stderr))
        else:
          dst_path = "%s/%s" % (backup_path, vmdisk_uuid)
          shutil.copyfile(src_path, dst_path)

  def import_image(self, image_uuid, image_url, ctr_name):
    """
    Imports an image from the specified URL and returns the vmdisk UUID.
    """
    payload = {
        "uuid": image_uuid,
        "imageImportSpec": {
          "url": image_url,
          "containerName": ctr_name,
        }
    }
    url = self.acro_url("images")
    r = self.session.post(url, data=json.dumps(payload))
    if r.status_code != requests.codes.ok:
      raise Exception("POST %s: %s" % (url, r.status_code))
    task_uuid = r.json()["taskUuid"]
    self.poll_task(task_uuid)

    url = self.acro_url("images/%s" % (image_uuid,))
    r = self.session.get(url)
    if r.status_code != requests.codes.ok:
      raise Exception("GET %s: %s" % (url, r.status_code))
    obj = r.json()
    return obj["vmDiskId"]

  def delete_image(self, image_uuid):
    """
    Deletes an image.
    """
    url = self.acro_url("images/%s" % (image_uuid,))
    r = self.session.delete(url)
    if r.status_code != requests.codes.ok:
      raise Exception("DELETE %s: %s" % (url, r.status_code))

  def restore_from_backup(self, vm_uuid, backup_path, ctr_name,
                          network_uuid=None, keep_mac_addresses=None):
    """
    Recovers a backup of a VM from a serialized descriptor and collection of
    disks, by copying the disks back to the cluster over NFS, and creating a
    new VM cloned from these disks.
    """
    print("Reading VM descriptor file")
    vm_info_file = os.path.join(backup_path, "vm.json")
    with open(vm_info_file) as fobj:
      vm_info = json.load(fobj)

    # Prepare a VM creation spec.
    payload = {
      "uuid": vm_uuid,
      "name": vm_info["config"]["name"],
      "numVcpus": vm_info["config"]["numVcpus"],
      "memoryMb": vm_info["config"]["memoryMb"],
      "vmNics": vm_info["config"].get("vmNics", []),
      "vmDisks": [],
    }

    # Override the network UUID.
    for vmnic in payload["vmNics"]:
      if network_uuid is not None:
        vmnic["networkUuid"] = network_uuid
      if not keep_mac_addresses:
        del vmnic["macAddress"]

    # Copy disk content to temporary files in the specified container.
    dst_path_list = []
    tmp_image_list = []
    try:
      for disk in vm_info["config"]["vmDisks"]:
        spec = {
          "isEmpty": disk["isEmpty"],
          "isCdrom": disk["isCdrom"],
          "diskAddress": {
            "deviceBus": disk["addr"]["deviceBus"],
            "deviceIndex": disk["addr"]["deviceIndex"],
          }
        }
        payload["vmDisks"].append(spec)
        if not disk["isEmpty"]:
          print("Copying data for disk %s" % (disk["id"],))
          src_path = "%s/%s" % (backup_path, disk["vmDiskUuid"])
          dst_path = (
              "/net/%s/%s/%s" %
              (self.cluster_ip, ctr_name, disk["vmDiskUuid"]))
          if not os.path.exists(src_path):
            create_image = True
            src_path += ".qcow2"
            dst_path += ".qcow2"
          else:
            create_image = False
          dst_path_list.append(dst_path)
          shutil.copyfile(src_path, dst_path)

          if create_image:
            print("Creating temporary image")
            image_uuid = str(uuid.uuid4())
            image_url = (
                "nfs://127.0.0.1/%s/%s.qcow2" % (ctr_name, disk["vmDiskUuid"]))
            tmp_image_list.append(image_uuid)
            vmdisk_uuid = self.import_image(image_uuid, image_url, ctr_name)
            spec["vmDiskClone"] = {
                "vmDiskUuid": vmdisk_uuid,
            }
          else:
            spec["vmDiskClone"] = {
                "imagePath": "/%s/%s" % (ctr_name, disk["vmDiskUuid"]),
            }

      # Create the VM by cloning disks.
      print("Creating VM %s" % (vm_uuid,))
      url = self.acro_url("vms")
      r = self.session.post(url, data=json.dumps(payload))
      if r.status_code != requests.codes.ok:
        raise Exception("POST %s: %s" % (url, r.status_code))

      task_uuid = r.json()["taskUuid"]
      self.poll_task(task_uuid)

    finally:
      print("Deleting temporary files")
      for dst_path in dst_path_list:
        if os.path.exists(dst_path):
          os.unlink(dst_path)

      if tmp_image_list:
        print("Deleting temporary images")
        for image_uuid in tmp_image_list:
          self.delete_image(image_uuid)

def backup(c):
  assert(FLAGS.vm_name is not None)
  vm_uuid = c.resolve_vm_uuid(FLAGS.vm_name)
  vm_info = c.get_vm_info(vm_uuid)
  snap_uuid = str(uuid.uuid4())
  c.create_snapshot(vm_uuid, snap_uuid)
  try:
    snap_info = c.get_snapshot_info(snap_uuid)
    c.create_backup(FLAGS.backup_path, snap_info, vm_info)
  finally:
    c.delete_snapshot(snap_uuid)

def restore(c):
  assert(FLAGS.restore_container)
  assert(FLAGS.restore_network_uuid)
  vm_uuid = str(uuid.uuid4())
  c.restore_from_backup(
      vm_uuid, FLAGS.backup_path, FLAGS.restore_container,
      network_uuid=FLAGS.restore_network_uuid,
      keep_mac_addresses=FLAGS.keep_mac_addresses)

def main():
  assert(FLAGS.action is not None)
  assert(FLAGS.cluster_ip is not None)
  assert(FLAGS.backup_path is not None)
  c = RestApiClient(FLAGS.cluster_ip, FLAGS.username, FLAGS.password)
  if FLAGS.action == "backup":
    backup(c)
  elif FLAGS.action == "restore":
    restore(c)
  else:
    raise Exception("Unknown --action; expected 'backup' or 'restore'")

if __name__ == "__main__":
  import sys
  gflags.FLAGS(sys.argv)
  sys.exit(main())
