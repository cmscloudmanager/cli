#!/usr/bin/env python

from os_setups.abstract_os_setup import AbstractOsSetup

REBOOT_REQUIRED_FILE="/run/reboot-required"

class UbuntuOsSetup(AbstractOsSetup):
  def __init__(self, server):
    self.server = server

    super().__init__()

  def update_server(self):
    for code in ["apt-get update", "apt-get -y upgrade"]:

      res = self.server.ssh_exec(code, False)

      if res.returncode != 0:
        fatal_error("{} failed".format(code))

    res = self.server.try_read_file(REBOOT_REQUIRED_FILE)

    if res.returncode != 0:
      print("can not read {}: {}".format(REBOOT_REQUIRED_FILE, res.stderr.decode("utf-8")))

      print("skipping reboot")

      return

    reboot_required = res.stdout.decode("utf-8")

    print("wait for server to reboot")

    # this is fine
    self.server.ssh_exec("echo 1 > /proc/sys/kernel/sysrq && echo s > /proc/sysrq-trigger && echo b > /proc/sysrq-trigger")

    self.server.wait_for_ssh(300)

  def install_ansible(self):
    for code in ["apt-get -y install ansible"]:

      res = self.server.ssh_exec(code, False)

      if res.returncode != 0:
        fatal_error("{} failed".format(code))
