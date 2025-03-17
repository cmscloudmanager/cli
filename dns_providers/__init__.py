from dns_providers.hetzner_dns_provider import HetznerDnsProvider

DNS_PROVIDER_TO_CLASS_MAP = {
    "hetzner": HetznerDnsProvider
}

class DnsProvider():
    def __init__(self, config, server_info):
        provider = DNS_PROVIDER_TO_CLASS_MAP[config.dns_provider_type]
        if provider == None:
            print("DnsProvider '{config.dns_provider_type}' is not implemented")
            sys.exit(1)
        self.provider = provider(config, server_info)

    def render_dns_config(self):
        return self.provider.render_dns_config()

    def get_hostnames(self):
        return self.provider.get_hostnames()
