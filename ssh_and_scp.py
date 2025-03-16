#!/usr/bin/env python

import os
from pathlib import Path
import subprocess
import sys
import time

SSH_WAIT_TIMEOUT_SECONDS = 3
WAIT_FOR_SSH_SLEEP_TIME_SECONDS = 1
KNOWN_HOSTS_FILE=Path.home() / ".cmscloudmanager_known_hosts"

class Ssh:
  @classmethod
  def keyscan(self, host, pipe_or_devnull = True):
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
      host], stdout=stdout, stderr=stderr)

    return res

  @classmethod
  def wait_reachable(self, host, max_wait_time_seconds):
    waiting_since = time.time_ns()

    while time.time_ns() < waiting_since + (max_wait_time_seconds * 10 ** 9):
      res = self.keyscan(host)

      if res.returncode == 0:
        return

      time.sleep(WAIT_FOR_SSH_SLEEP_TIME_SECONDS)

    print_error("wait for ssh failed: ssh-keycan {} failed: {}".format(host, res.stderr.decode("utf-8")))

    return 1

  @classmethod
  def prepare_known_hosts_file(self, host):
    res = self.keyscan(host)

    if res.returncode != 0:
      print_error("ssh-keycan {} failed: {}".format(host, res.stderr.decode("utf-8")))

      exit(2)

    with open(KNOWN_HOSTS_FILE, "w") as file:
      file.write(res.stdout.decode("utf-8"))

  @classmethod
  def exec(self, host, code, pipe = True):
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
      host,
      "/usr/bin/env", "bash"], input=code.encode("utf-8"), stdout=stdout, stderr=stderr)

    return res

  @classmethod
  def check_connect(self, host):
    res = self.exec(host, "true")

    if res.returncode != 0:
      fatal_error("can not connect {} via ssh: {}".format(host, res.stderr.decode("utf-8")))

  @classmethod
  def try_read_file(self, host, file):
    res = self.exec(host, "cat {}".format(file))

    return res

  @classmethod
  def upload_dir(self, host, dir):
    # remove remains of previous runs
    self.exec(host, "test -e {} && rm -r {}".format(dir, dir))

    res = subprocess.run([
      "/usr/bin/env",
      "scp",
      "-o", "PasswordAuthentication=no",
      "-o", "User=root",
      "-o", "UserKnownHostsFile={}".format(KNOWN_HOSTS_FILE),
      "-r",
      os.path.join(os.path.dirname(__file__), dir),
      "{}:./{}".format(host, dir)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if res.returncode != 0:
      fatal_error("scp {} to {} failed: {}".format(dir, host, res.stderr.decode("utf-8")))
