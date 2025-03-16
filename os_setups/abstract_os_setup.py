#!/usr/bin/env python

from abc import ABC, abstractmethod

class AbstractOsSetup(ABC):
  @abstractmethod
  def update_server(self):
    pass

  @abstractmethod
  def install_ansible(self):
    pass

  @abstractmethod
  def install_dnsutils(self):
    pass
