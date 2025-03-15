#!/usr/bin/env python

from pathlib import Path
import subprocess
import sys
import time

SSH_MAX_WAIT_TIME_SECONDS = 5 # 120
SSH_WAIT_TIMEOUT_SECONDS = 3
WAIT_FOR_SSH_SLEEP_TIME_SECONDS = 1
KNOWN_HOSTS_FILE=Path.home() / ".cmscloudmanager_known_hosts"

def wait_for_ssh(host):
  waiting_since = time.time_ns()

  while time.time_ns() < waiting_since + (SSH_MAX_WAIT_TIME_SECONDS * 10 ** 6):
    res = subprocess.run(["/usr/bin/env", "ssh-keyscan", "-H", "-T", str(SSH_WAIT_TIMEOUT_SECONDS), host], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if res.returncode == 0:
      return

    time.sleep(WAIT_FOR_SSH_SLEEP_TIME_SECONDS)

  print("wait for ssh failed", file=sys.stderr)

  return 1

def ssh_keyscan(host):
  res = subprocess.run(["/usr/bin/env", "ssh-keyscan", "-H", "-T", str(SSH_WAIT_TIMEOUT_SECONDS), host], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  if res.returncode != 0:
    print("ssh-keycan {} failed: {}".format(host, res.stderr.decode("utf-8")), file=sys.stderr)

    return 1

  return res.stdout.decode("utf-8")

def prepare_known_hosts_file(host):
  known_hosts = ssh_keyscan(host)

  with open(KNOWN_HOSTS_FILE, "w") as file:
    file.write(known_hosts)

def ssh_exec(host, code):
  res = subprocess.run(["/usr/bin/env", "ssh", "-o", "PasswordAuthentication=no", "-o", "UserKnownHostsFile={}".format(KNOWN_HOSTS_FILE), "-l", "root", host, "/usr/bin/env", "bash"], input=code.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  return res

def main():
  host = "65.108.217.90"

  print("setting up server {} for ansible".format(host))

  print("waiting for server to respond to ssh")

  wait_for_ssh(host)

  prepare_known_hosts_file(host)

  res = ssh_exec(host, "true")

  if res.returncode != 0:
    print("fatal error: can not connect server via ssh: {}".format(res.stderr.decode("utf-8")), file=sys.stderr)

    return res.returncode

  print("updating server")

  for code in ["apt-get update", "apt-get -y upgrade", "apt-get -y install ansible"]:

    res = ssh_exec(host, code)

    if res.returncode != 0:
      print("fatal error: {} failed: {}".format(code ,res.stderr.decode("utf-8")))

      return 1

  print("installing ansible")

  for code in ["apt-get -y install ansible"]:

    res = ssh_exec(host, code)

    if res.returncode != 0:
      print("fatal error: {} failed: {}".format(code ,res.stderr.decode("utf-8")))

      return 1

main()
