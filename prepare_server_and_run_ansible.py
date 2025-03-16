#!/usr/bin/env python

import os
from pathlib import Path
import subprocess
import sys
import time

SSH_MAX_WAIT_TIME_SECONDS = 120
SSH_WAIT_TIMEOUT_SECONDS = 3
WAIT_FOR_SSH_SLEEP_TIME_SECONDS = 1
KNOWN_HOSTS_FILE=Path.home() / ".cmscloudmanager_known_hosts"
LSB_RELEASE_FILE = "/etc/lsb-release"
DISTRIB_ID_OS_MODULE_MAP = {
  "Ubuntu": "ubuntu_specifics"
}

def print_step(step):
  print("\033[90m{}\033[0m".format(step))

def print_error(message):
  print("\033[91m{}\033[0m".format(message), file=sys.stderr)

def fatal_error(message):
  print_error(message)
  exit(1)

class Server:
  def __init__(self, host):
    self.host = host

  def ssh_keyscan(self, pipe_or_devnull = True):
    if pipe_or_devnull:
      stdout = subprocess.PIPE
      stderr = subprocess.PIPE
    else:
      stdout = subprocess.DEVNULL
      stderr = subprocess.DEVNULL

    res = subprocess.run([
      "/usr/bin/env",
      "ssh-keyscan",
      "-H",
      "-T", str(SSH_WAIT_TIMEOUT_SECONDS),
      self.host], stdout=stdout, stderr=stderr)

    return res

  def wait_for_ssh(self):
    waiting_since = time.time_ns()

    while time.time_ns() < waiting_since + (SSH_MAX_WAIT_TIME_SECONDS * 10 ** 6):
      res = self.ssh_keyscan(False)

      if res.returncode == 0:
        return

      time.sleep(WAIT_FOR_SSH_SLEEP_TIME_SECONDS)

    print_error("wait for ssh failed: ssh-keycan {} failed: {}".format(self.host, res.stderr.decode("utf-8")))

    return 1

  def prepare_known_hosts_file(self):
    res = self.ssh_keyscan()

    if res.returncode != 0:
      print_error("ssh-keycan {} failed: {}".format(self.host, res.stderr.decode("utf-8")))

      exit(2)

    with open(KNOWN_HOSTS_FILE, "w") as file:
      file.write(res.stdout.decode("utf-8"))

  def ssh_exec(self, code, pipe = True):
    if pipe:
      stdout = subprocess.PIPE
      stderr = subprocess.PIPE
    else:
      stdout = None
      stderr = None

    res = subprocess.run([
      "/usr/bin/env",
      "ssh",
      "-o", "PasswordAuthentication=no",
      "-o", "UserKnownHostsFile={}".format(KNOWN_HOSTS_FILE),
      "-l", "root",
      self.host,
      "/usr/bin/env", "bash"], input=code.encode("utf-8"), stdout=stdout, stderr=stderr)

    return res

  def check_ssh_connect(self):
    res = self.ssh_exec("true")

    if res.returncode != 0:
      fatal_error("fatal error: can not connect {} via ssh: {}".format(self.host, res.stderr.decode("utf-8")))

  def detect_os_specific_module(self):
    res = self.ssh_exec("cat {}".format(LSB_RELEASE_FILE))

    if res.returncode != 0:
      fatal_error("fatal error: can not read {}: {}".format(LSB_RELEASE_FILE, res.stderr.decode("utf-8")))

    distrib_id = None

    for line in res.stdout.decode("utf-8").split("\n"):
      if line.startswith("DISTRIB_ID="):
        distrib_id = line[11:]

    if not distrib_id or not distrib_id in DISTRIB_ID_OS_MODULE_MAP:
      fatal_error("fatal error: distrib id {} is unknown".format(str(distrib_id)))

    os_specific_module = DISTRIB_ID_OS_MODULE_MAP[distrib_id]

    return os_specific_module

  def update_server(self):
    for code in ["apt-get update", "apt-get -y upgrade"]:

      res = self.ssh_exec(code, False)

      if res.returncode != 0:
        fatal_error("fatal error: {} failed".format(code))

  def install_ansible(self):
    for code in ["apt-get -y install ansible"]:

      res = self.ssh_exec(code, False)

      if res.returncode != 0:
        fatal_error("fatal error: {} failed".format(code))

  def upload_ansible_dir(self):
    # remove remains of previous runs
    self.ssh_exec("test -e ansible && rm -r ansible")

    res = subprocess.run([
      "/usr/bin/env",
      "scp",
      "-o", "PasswordAuthentication=no",
      "-o", "User=root",
      "-o", "UserKnownHostsFile={}".format(KNOWN_HOSTS_FILE),
      "-r",
      os.path.join(os.path.dirname(__file__), "ansible"),
      "{}:./ansible".format(self.host)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if res.returncode != 0:
      fatal_error("fatal error: scp ansible to {} failed: {}".format(self.host, res.stderr.decode("utf-8")))

  def install_ansible_requirements(self):
    res = self.ssh_exec("cd ansible && ansible-galaxy install -r requirements.yml -p roles -f", False)

    if res.returncode != 0:
      fatal_error("fatal error: installing ansible requirements failed")

  def run_ansible(self):
    res = self.ssh_exec("cd ansible && ansible-playbook --connection=local --inventory 127.0.0.1, playbook.yml -e letsencrypt_email=something@example.com", False)

    if res.returncode != 0:
      fatal_error("fatal error: running ansible failed")

  def prepare_server_and_run_ansible(self):
    print_step("setting up {} for ansible".format(self.host))

    print_step("waiting for server to respond to ssh")

    self.wait_for_ssh()

    self.prepare_known_hosts_file()

    self.check_ssh_connect()

    self.detect_os_specific_module()

    print_step("updating server")

    self.update_server()

    print_step("installing ansible")

    self.install_ansible()

    print_step("uploading ansible code")

    self.upload_ansible_dir()

    print_step("installing ansible requirements")

    self.install_ansible_requirements()

    print_step("running ansible")

    self.run_ansible()

if __name__ == "__main__":
  server = Server(sys.argv[1])

  server.prepare_server_and_run_ansible()
