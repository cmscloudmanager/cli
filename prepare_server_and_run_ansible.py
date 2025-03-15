#!/usr/bin/env python

import os
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

def ssh_exec(host, code, pipe = True):
  if pipe:
    stdout = subprocess.PIPE
    stderr = subprocess.PIPE
  else:
    stdout = None
    stderr = None

  res = subprocess.run(["/usr/bin/env", "ssh", "-o", "PasswordAuthentication=no", "-o", "UserKnownHostsFile={}".format(KNOWN_HOSTS_FILE), "-l", "root", host, "/usr/bin/env", "bash"], input=code.encode("utf-8"), stdout=stdout, stderr=stderr)

  return res

def prepare_server_and_run_ansible(host):
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

    res = ssh_exec(host, code, False)

    if res.returncode != 0:
      print("fatal error: {} failed".format(code), file=sys.stderr)

      return 1

  print("installing ansible")

  for code in ["apt-get -y install ansible"]:

    res = ssh_exec(host, code, False)

    if res.returncode != 0:
      print("fatal error: {} failed".format(code), file=sys.stderr)

      return 1

  print("installing ansible requirements")

  res = ssh_exec(host, "cd ansible && ansible-galaxy install -r requirements.yml -p roles -f", False)

  if res.returncode != 0:
    print("fatal error: installing ansible requirements failed", file=sys.stderr)

    return 1

  print("uploading ansible playbook")

  res = subprocess.run([
    "/usr/bin/env",
    "scp",
    "-o", "PasswordAuthentication=no",
    "-o", "User=root",
    "-o", "UserKnownHostsFile={}".format(KNOWN_HOSTS_FILE),
    "-r",
    os.path.join(os.path.dirname(__file__), "ansible"),
    "{}:./ansible".format(host)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

  if res.returncode != 0:
    print("fatal error: scp ansible failed: {}".format(code ,res.stderr.decode("utf-8")), file=sys.stderr)

    return 1

  print("running ansible")

  res = ssh_exec(host, "cd ansible && ansible-playbook --connection=local --inventory 127.0.0.1, playbook.yml -e letsencrypt_email=something@example.com", False)

  if res.returncode != 0:
    print("fatal error: running ansbible failed", file=sys.stderr)

if __name__ == "__main__":
  prepare_server_and_run_ansible(sys.argv[1])
