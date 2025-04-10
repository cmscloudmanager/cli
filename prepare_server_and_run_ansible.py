#!/usr/bin/env python

import requests
import sys
import time

from ssh_and_scp import Ssh
from os_setups import OsSetup

SSH_MAX_WAIT_TIME_SECONDS = 120
LSB_RELEASE_FILE = "/etc/lsb-release"
DEBIAN_VERSION_FILE="/etc/debian_version"
ANSIBLE_COMMANDLINE = "ansible-playbook --connection=local --inventory 127.0.0.1, playbook.yml"
ANSIBLE_GALAXY_INSTALL_COMMANDLINE = "ansible-galaxy install -r requirements.yml -p roles -f"
DNSCONTROL_COMMANDLINE = "docker run --rm -v ./dns:/dns ghcr.io/stackexchange/dnscontrol push"

def print_step(step):
  print("\033[90m{}\033[0m".format(step))

def print_error(message):
  print("\033[91m{}\033[0m".format(message), file=sys.stderr)

def fatal_error(message):
  print_error("fatal error: {}".format(message))
  exit(1)

class Server:
  def __init__(self, host):
    self.host = host

  def try_read_distrib_id(self):
    res = Ssh.try_read_file(self.host, LSB_RELEASE_FILE)

    if res.returncode != 0:
      res = Ssh.try_read_file(self.host, DEBIAN_VERSION_FILE)

      if res.returncode == 0:
        distrib_id = 'Debian'
      else:
        fatal_error("can not read {} or {}: {}".format(LSB_RELEASE_FILE, DEBIAN_VERSION_FILE, res.stderr.decode("utf-8")))

    distrib_id = None

    for line in res.stdout.decode("utf-8").split("\n"):
      if line.startswith("DISTRIB_ID="):
        distrib_id = line[11:]

    return distrib_id

  def install_ansible_requirements(self):
    res = Ssh.exec(self.host, "cd ansible && {}".format(ANSIBLE_GALAXY_INSTALL_COMMANDLINE), False)

    if res.returncode != 0:
      fatal_error("installing ansible requirements failed")

  def run_ansible(self):
    res = Ssh.exec(self.host, "cd ansible && {}".format(ANSIBLE_COMMANDLINE), False)

    if res.returncode != 0:
      fatal_error("running ansible failed")

  def prepare_server_and_run_ansible(self):
    print_step("setting up {} for ansible".format(self.host))

    print_step("waiting for server to respond to ssh")

    Ssh.wait_reachable(self.host, SSH_MAX_WAIT_TIME_SECONDS)

    Ssh.prepare_known_hosts_file(self.host)

    Ssh.check_connect(self.host)

    distrib_id = self.try_read_distrib_id()

    os_setup = OsSetup(distrib_id, self)

    print_step("updating server")

    os_setup.update_server()

    print_step("installing ansible")

    os_setup.install_ansible()

    os_setup.install_dnsutils()

    print_step("uploading ansible config")

    Ssh.upload_dir(self.host, "ansible")

    print_step("installing ansible requirements")

    self.install_ansible_requirements()

    print_step("running ansible")

    self.run_ansible()

  def run_dnscontrol(self):
    print_step("uploading dns config")

    Ssh.upload_dir(self.host, "dns")

    print_step("deploying dns")

    Ssh.exec(self.host, DNSCONTROL_COMMANDLINE, False)

  def wait_for_dns(self, dns, ips = []):
    splitdns = dns.split(".")

    zone = ".".join(splitdns[-2:])
    name = ".".join(splitdns[:-2])

    ipv4s = []
    ipv6s = []

    record_types = []

    for ip in ips:
      if "." in ip:
        ipv4s.append(ip)

        if "A" not in record_types:
          record_types.append("A")

        continue

      if ":" in ip:
        ipv6s.append(ip)

        if "AAAA" not in record_types:
          record_types.append("AAAA")

    res = Ssh.exec(self.host, "dig +short NS {}".format(zone))

    if res.returncode != 0:
      fatal_error("dig NS {} failed: {}".format(zone, res.stderr.decode("utf-8")))

      return

    nameservers = res.stdout.decode("utf-8").split("\n")[:-1]

    waiting_since = time.time_ns()

    while time.time_ns() < waiting_since + (300 * 10 ** 9):
      record_types_ok = []

      for record_type in record_types:
        ok_nameservers = []

        for nameserver in nameservers:
          res = Ssh.exec(self.host, "dig @{} +short {} {}".format(nameserver, record_type, dns))

          if res.returncode != 0:
            fatal_error("dig {} {} failed: {}".format(record_type, dns, res.stderr.decode("utf-8")))

          if record_type == 'A':
            record_type_ips = ipv4s
          else:
            record_type_ips = ipv6s

          if set(record_type_ips).issubset(set(res.stdout.decode("utf-8").split("\n")[:-1])):
            print("nameserver {} record type {} OK".format(nameserver, record_type))
            ok_nameservers.append(nameserver)

        if ok_nameservers == nameservers:
          record_types_ok.append(record_type)

        if record_types_ok == record_types:
          return

      time.sleep(2)

    fatal_error("wait for dns failed")

  def restart_reverse_proxy(self):
    res = Ssh.exec(self.host, "systemctl restart docker-compose@reverse-proxy")

    if res.returncode != 0:
      fatal_error("restarting reverse proxy failed: {}".format(res.stderr.decode("utf-8")))

if __name__ == "__main__":
  server = Server(sys.argv[1])

  # server.prepare_server_and_run_ansible()

  # server.run_dnscontrol()

  dns = "test.cfhackathontest.com"

  server.wait_for_dns(dns, [])

  # print(requests.get("https://{}".format(dns)).text)
