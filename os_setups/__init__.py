#!/usr/bin/env python

from os_setups.ubuntu_os_setup import UbuntuOsSetup

DISTRIB_ID_TO_CLASS_MAP = {
  "Ubuntu": UbuntuOsSetup
}

class OsSetup():
  def __init__(self, distrib_id, server):
    self.server = server

    os_setup = DISTRIB_ID_TO_CLASS_MAP[distrib_id]

    if os_setup == None:
      print("Adapter '{distrib_id}' is not implemented")

      sys.exit(1)

    self.os_setup = os_setup(server)

  def update_server(self):
    return self.os_setup.update_server()

  def install_ansible(self):
    return self.os_setup.install_ansible()
