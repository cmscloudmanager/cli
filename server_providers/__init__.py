from server_providers.hetzner_cloud_server_provider import HetznerCloudServerProvider

SERVER_PROVIDER_TO_CLASS_MAP = {
    "hetzner-cloud": HetznerCloudServerProvider
}

class ServerProvider():
    def __init__(self, config):
        self.config = config
        provider = SERVER_PROVIDER_TO_CLASS_MAP[config.server_provider_type]
        if provider == None:
            print("ServerProvider '{config.server_provider_type}' is not implemented")
            sys.exit(1)
        self.provider = provider(config)

    def fetch_provisioned_server(self):
        return self.provider.fetch_provisioned_server()

    def provision_server(self):
        return self.provider.provision_server()

