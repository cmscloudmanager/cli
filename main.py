#!/usr/bin/env python

from hcloud import Client
from hcloud.images import Image
from hcloud.server_types import ServerType
from abc import ABC, abstractmethod

import base64
import hashlib
import yaml
import click
import sys

class Component:
    name: str
    component_type: str
    config: dict

    def __init__(self, name, component_type, config):
        self.name = name
        self.component_type = component_type
        self.config = config

class Configuration:
    provider: str
    api_key: str
    instance: str
    server_name: str
    uuid: str
    image: str
    ssh_pub_key: str
    components: [Component]

    def __init__(self, provider, api_key, instance, server_name, uuid, image, ssh_pub_key):
        self.provider = provider
        self.api_key = api_key
        self.instance = instance
        self.server_name = server_name
        self.uuid = uuid
        self.image = image
        self.ssh_pub_key = ssh_pub_key

    @classmethod
    def from_manifest(cls, file_name):
        with open(file_name) as stream:
            try:
                yml = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                click.echo(exc)
        components = []
        for component in yml['components']:
            components.append(Component(component['name'], component['type'], component['config']))
            
        return cls(yml['provider'], yml['api_key'], yml['instance'], yml['server_name'], yml['uuid'], yml['image'], yml['ssh_pub_key'])


class HostingProviderAdapter(ABC):
    @abstractmethod
    def register_ssh_pub_key(self):
        pass

    @abstractmethod
    def create_server(self):
        pass

class HetznerAdapter(HostingProviderAdapter):
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
        return self.client.ssh_keys.create("Patrick SSH Key", self.config.ssh_pub_key, {})

    def create_server(self):
        self.client = Client(token=self.config.api_key)

        ssh_key = self.__fetch_ssh_key_by_pub_key()

        if ssh_key == None:
            ssh_key = self.register_ssh_pub_key()

        image_name = self.__map_image_to_os_image()

        self.client.servers.create(
            name=self.config.server_name,
            server_type=ServerType(name=self.config.instance),
            image=Image(name=image_name),
            ssh_keys=[ssh_key],
            labels={'deployment_uuid': self.config.uuid}
        )

PROVIDER_TO_CLASS_MAP = {
    "hetzner": HetznerAdapter
}

def fetch_adapter_from_config(config):
    adapter = PROVIDER_TO_CLASS_MAP[config.provider]

    if adapter == None:
        print(f"Provider {config.provider} is not implemented")
        sys.exit(1)

    return adapter

@click.group()
def cli():
    pass

@cli.command()
@click.argument('file_name', type=click.Path(exists=True))
def deploy(file_name):
    config = Configuration.from_manifest(file_name)

    adapter_class = fetch_adapter_from_config(config)
    adapter = adapter_class(config)

    adapter.create_server()

if __name__ == '__main__':
    cli()
