import yaml

class Configuration:
    provider: str
    api_key: str
    instance: str
    server_name: str
    uuid: str
    image: str
    ssh_pub_key: str

    def __init__(self, provider, api_key, instance, server_name, uuid, image, ssh_pub_key, lets_encrypt_email, components):
        self.provider = provider
        self.api_key = api_key
        self.instance = instance
        self.server_name = server_name
        self.uuid = uuid
        self.image = image
        self.ssh_pub_key = ssh_pub_key
        self.lets_encrypt_email = lets_encrypt_email
        self.components = components

    @classmethod
    def from_manifest(cls, file_name):
        with open(file_name) as stream:
            try:
                yml = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                click.echo(exc)
            
        return cls(yml['provider']['type'], yml['provider']['api_key'], yml['instance'], yml['server_name'], yml['uuid'], yml['image'], yml['ssh_pub_key'], yml['lets_encrypt_email'], yml['components'])

    def render_ansible_vars(self):
        variables = {
            "lets_encrypt_email": self.lets_encrypt_email,
            "docker_compose_services": self.components
        }

        with open('ansible/group_vars/all/vars.yml', 'w') as outfile:
            yaml.dump(variables, outfile, default_flow_style=False)
