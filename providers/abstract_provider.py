from abc import ABC, abstractmethod

class AbstractProvider(ABC):
    @abstractmethod
    def register_ssh_pub_key(self):
        pass

    @abstractmethod
    def provision_server(self):
        pass

