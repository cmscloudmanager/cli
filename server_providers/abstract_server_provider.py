from abc import ABC, abstractmethod

class AbstractServerProvider(ABC):
    @abstractmethod
    def register_ssh_pub_key(self):
        pass

    @abstractmethod
    def fetch_provisioned_server(self):
        pass

    @abstractmethod
    def provision_server(self):
        pass

