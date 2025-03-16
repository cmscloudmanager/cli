from configuration import Configuration
from dns_providers.abstract_dns_provider import AbstractDnsProvider
from server_information import ServerInformation

import yaml
import json

class HetznerDnsProvider(AbstractDnsProvider):
    config: Configuration
    server_info: ServerInformation

    def __init__(self, config, server_info):
        self.config = config
        self.server_info = server_info
        super().__init__()

    def get_hostnames(self):
        hostnames = []
        for component in self.config.components:
            if "config" in component and "hostname" in component["config"]:
                hostnames.append(component["config"]["hostname"])
        return hostnames

    def __get_zone_config_from_components(self):
        zones = {}
        for hostname in self.get_hostnames():
            arr = hostname.split(".")
            zone = ".".join(arr[-2:])
            name = ".".join(arr[:-2])
            if zone not in zones:
                zones[zone] = []
            zones[zone].append(name)
        return zones

    def render_dns_config(self):
        zones = self.__get_zone_config_from_components()
        content = ""
        for zone, names in zones.items():
            content += f"D('{zone}', NewRegistrar('none', 'NONE'), DnsProvider(NewDnsProvider('hetzner', 'HETZNER')), NO_PURGE,\n"
            for name in names:
                if self.server_info.ipv4 != None:
                    content += f"  A('{name}', '{self.server_info.ipv4}'), \n"
                if self.server_info.ipv6 != None:
                    net = self.server_info.ipv6.split('/')[0]
                    content += f"  AAAA('{name}', '{net}1'), \n"

            content += f");\n"

        with open('dns/dnsconfig.js', 'w') as outfile:
            outfile.write(content)
        with open('dns/creds.json', 'w') as outfile:
            data = json.dumps({"hetzner": {"TYPE": "HETZNER", "api_key": self.config.dns_provider_api_key}})
            outfile.write(data)


