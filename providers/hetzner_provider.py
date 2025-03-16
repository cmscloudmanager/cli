from configuration import Configuration
from hcloud import Client
from hcloud.images import Image
from hcloud.server_types import ServerType

from providers.abstract_provider import AbstractProvider

import base64
import hashlib

class HetznerProvider(AbstractProvider):
    config: Configuration
    client: Client

    def __init__(self, config):
        self.config = config
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

    def provision_server(self):
        self.client = Client(token=self.config.api_key)

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

        return response.server.public_net.primary_ipv4.ip
