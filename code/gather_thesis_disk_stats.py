#! /usr/bin/python
# Author: tallen@nutanix.com

import sys, os
import urllib2
import fileinput

cvm_ip = sys.argv[1]

NCLI_TIER_USAGE_CMD = "ncli disk ls tier-name=SSD-SATA"

def get_ssd_tier_usages(ncli_output):
  """
  For the SSD tier, returns a mapping from node IP (or 'all') to tuple of (max
  capacity, used capacity, free capacity).
  """
  def get_byte_str(s):
    s = s.strip()
    if "(" in s:
      return s.split('(')[1].split('bytes')[0].strip().replace(',', '')
    else:
      return s.split('bytes')[0].split(":")[1].strip().replace(',', '')

  def get_ip_str(s):
    s = s.strip()
    return s.strip().split(":")[1].strip()

  node_map = {}

  total_max_capacity = 0
  total_used_capacity = 0
  total_free_capacity = 0

  max_capacity = 0
  used_capacity = 0
  free_capacity = 0
  ip = ""
  for line in ncli_output:
    if line.strip().startswith("Max Capacity"):
      max_capacity = int(get_byte_str(line))
      total_max_capacity += max_capacity
    elif line.strip().startswith("Used Capacity"):
      used_capacity = int(get_byte_str(line))
      total_used_capacity += used_capacity
    elif line.strip().startswith("Free Capacity"):
      free_capacity = int(get_byte_str(line))
      total_free_capacity += free_capacity
    elif line.strip().startswith("Controller VM Address"):
      ip = get_ip_str(line)
      node_map[ip] = (max_capacity, used_capacity, free_capacity)
      max_capacity = 0
      used_capacity = 0
      free_capacity = 0
      ip = ""

  node_map["all"] = (
    (total_max_capacity, total_used_capacity, total_free_capacity))
  return node_map

def parse_disk_stats_page(cvm_ip):
  req = urllib2.Request('http://' + cvm_ip + ':2009/disk_stats')
  response = urllib2.urlopen(req)
  page_data = response.readlines()
  page_data = filter(lambda x: x.startswith("Disk-") or
                               "Count" in x or
                               "Migration" in x,
                     page_data)

  # Map disk ID to read/write tuple.
  disk_access_map = {}
  disk_id = -1
  count_counter = 0
  for line in page_data:
    if line.startswith("Disk-"):
      # Disk ID
      disk_id = line.split("-")[1].split("<")[0]
      disk_access_map[disk_id] = (None, None)
      count_counter = 0
      continue
    elif "Count:" in line:
      if count_counter == 1:
        # Reads
        tup = disk_access_map[disk_id]
        disk_access_map[disk_id] = (
          int(line.split(":")[1].split("<")[0].strip()), tup[1])
      elif count_counter == 2:
        # Writes
        tup = disk_access_map[disk_id]
        disk_access_map[disk_id] = (
          tup[0], int(line.split(":")[1].split("<")[0].strip()))
      count_counter += 1
    elif "Migration" in line:
      break
  return disk_access_map

usages = get_ssd_tier_usages(sys.stdin.readlines())
file_map = {}
for key in usages.keys():
  file_map[key] = open(key + ".txt", "a")
for key in usages.keys():
  usage_str = ",".join(map(lambda x: str(x), usages[key]))
  file_map[key].write(usage_str + "\n")
