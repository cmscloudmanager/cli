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

def print_step(step):
  print("\033[90m{}\033[0m".format(step))

def print_error(message):
  print("\033[91m{}\033[0m".format(message), file=sys.stderr)

class Renameme:
  def __init__(self, host):
    self.host = host

  def wait_for_ssh(self):
    waiting_since = time.time_ns()

    while time.time_ns() < waiting_since + (SSH_MAX_WAIT_TIME_SECONDS * 10 ** 6):
      res = subprocess.run(["/usr/bin/env", "ssh-keyscan", "-H", "-T", str(SSH_WAIT_TIMEOUT_SECONDS), self.host], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

      if res.returncode == 0:
        return

      time.sleep(WAIT_FOR_SSH_SLEEP_TIME_SECONDS)

    print_error("wait for ssh failed")

    exit(1)

  def ssh_keyscan(self):
    res = subprocess.run(["/usr/bin/env", "ssh-keyscan", "-H", "-T", str(SSH_WAIT_TIMEOUT_SECONDS), self.host], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if res.returncode != 0:
      print_error("ssh-keycan {} failed: {}".format(self.host, res.stderr.decode("utf-8")))

      exit(2)

    return res.stdout.decode("utf-8")

  def prepare_known_hosts_file(self):
    known_hosts = self.ssh_keyscan()

    with open(KNOWN_HOSTS_FILE, "w") as file:
      file.write(known_hosts)

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

  def update_server(self):
    for code in ["apt-get update", "apt-get -y upgrade", "apt-get -y install ansible"]:

      res = self.ssh_exec(code, False)

      if res.returncode != 0:
        print_error("fatal error: {} failed".format(code))

        exit(4)

  def install_ansible(self):
    for code in ["apt-get -y install ansible"]:

      res = self.ssh_exec(code, False)

      if res.returncode != 0:
        print_error("fatal error: {} failed".format(code))

        exit(5)

  def upload_ansible_code(self):
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
      print_error("fatal error: scp ansible failed: {}".format(code ,res.stderr.decode("utf-8")))

      exit(6)

  def install_ansible_requirements(self):
    res = self.ssh_exec("cd ansible && ansible-galaxy install -r requirements.yml -p roles -f", False)

    if res.returncode != 0:
      print_error("fatal error: installing ansible requirements failed")

      exit(7)

  def run_ansible(self):
    res = self.ssh_exec("cd ansible && ansible-playbook --connection=local --inventory 127.0.0.1, playbook.yml -e letsencrypt_email=something@example.com", False)

    if res.returncode != 0:
      print_error("fatal error: running ansbible failed")

  def prepare_server_and_run_ansible(self):
    print("\033[95msetting up server {} for ansible\033[0m".format(self.host))

    print_step("waiting for server to respond to ssh")

    self.wait_for_ssh()

    self.prepare_known_hosts_file()

    res = self.ssh_exec("true")

    if res.returncode != 0:
      print_error("fatal error: can not connect server via ssh: {}".format(res.stderr.decode("utf-8")))

      exit(3)

    print_step("updating server")

    self.update_server()

    print_step("installing ansible")

    self.install_ansible()

    print_step("uploading ansible code")

    self.upload_ansible_code()

    print_step("installing ansible requirements")

    self.install_ansible_requirements()

    print_step("running ansible")

    self.run_ansible()

if __name__ == "__main__":
  server = Server(sys.argv[1])

  server.prepare_server_and_run_ansible()
