from abc import ABC, abstractmethod

class AbstractDnsProvider(ABC):
    @abstractmethod
    def render_dns_config(self):
        pass

