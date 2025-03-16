from providers.hetzner_provider import HetznerProvider

PROVIDER_TO_CLASS_MAP = {
    "hetzner": HetznerProvider
}

class ServerProvider():
    def __init__(self, config):
        self.config = config
        provider = PROVIDER_TO_CLASS_MAP[config.provider]
        if provider == None:
            print("Adapter '{config.provider}' is not implemented")
            sys.exit(1)
        self.provider = provider(config)

    def fetch_provisioned_server_ip(self):
        return self.provider.fetch_provisioned_server_ip()

    def provision_server(self):
        return self.provider.provision_server()

