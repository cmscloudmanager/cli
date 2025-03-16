import yaml

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

