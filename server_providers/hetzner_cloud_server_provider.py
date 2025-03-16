from configuration import Configuration
from hcloud import Client
from hcloud.images import Image
from hcloud.server_types import ServerType

from server_providers.abstract_server_provider import AbstractServerProvider
from server_information import ServerInformation

import base64
import hashlib
import sys

class HetznerCloudServerProvider(AbstractServerProvider):
    config: Configuration
    client: Client

    def __init__(self, config):
        self.config = config
        self.client = Client(token=self.config.server_provider_api_key)
        super().__init__()

    def __fetch_ssh_key_by_pub_key(self):
        key = base64.b64decode(self.config.ssh_pub_key.strip().split()[1].encode('ascii'))
        fp_plain = hashlib.md5(key).hexdigest()
        fingerprint = ':'.join(a+b for a,b in zip(fp_plain[::2], fp_plain[1::2]))
        return self.client.ssh_keys.get_by_fingerprint(fingerprint)

    def __map_image_to_os_image(self):
        image = {
            "debian": "debian-12",
            "ubuntu": "ubuntu-24.04"
        }[self.config.image]

        return image

    def register_ssh_pub_key(self):
        return self.client.ssh_keys.create(f"{self.config.server_name} Key", self.config.ssh_pub_key, {})

    def fetch_provisioned_server(self):
        servers = self.client.servers.get_all(label_selector=f"deployment_uuid={self.config.uuid}")

        length = len(servers)

        if length == 1:
            server = servers[0]
            ipv4 = server.public_net.primary_ipv4.ip
            ipv6 = server.public_net.primary_ipv6.ip
            return ServerInformation(ipv4, ipv6)

        if length == 0:
            return None

        print("Multiple servers with same deployment_uuid found. Aborting!")
        sys.exit(1)

    def provision_server(self):
        ssh_key = self.__fetch_ssh_key_by_pub_key()

        if ssh_key == None:
            ssh_key = self.register_ssh_pub_key()

        image_name = self.__map_image_to_os_image()

        response = self.client.servers.create(
            name=self.config.server_name,
            server_type=ServerType(name=self.config.instance),
            image=Image(name=image_name),
            ssh_keys=[ssh_key],
            labels={'deployment_uuid': self.config.uuid}
        )

        ipv4 = response.server.public_net.primary_ipv4.ip
        ipv6 = response.server.public_net.primary_ipv6.ip
        return ServerInformation(ipv4, ipv6)
