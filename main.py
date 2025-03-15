#!/usr/bin/env python

from hcloud import Client
from hcloud.images import Image
from hcloud.server_types import ServerType
import base64
import hashlib
import yaml

API_KEY = "..."
SSH_PUB_KEY = "..."

def main():
    client = Client(token=API_KEY)

    if is_ssh_key_already_registered(client, SSH_PUB_KEY):
        print("SSH KEY is already registered.")
    else:
        print("SSH KEY is NOT registered")
        register_ssh_pub_key(client, SSH_PUB_KEY)
        print("SSH KEY now registered")

    return create_server(client, "patrick-test", "cpx11", "debian-12", SSH_PUB_KEY)

def fingerprint_ssh_pub_key(pub_key):
    key = base64.b64decode(pub_key.strip().split()[1].encode('ascii'))
    fp_plain = hashlib.md5(key).hexdigest()
    return ':'.join(a+b for a,b in zip(fp_plain[::2], fp_plain[1::2]))

def fetch_ssh_key_object_for_pub_key(client, ssh_pub_key):
    fingerprint = fingerprint_ssh_pub_key(ssh_pub_key)
    return client.ssh_keys.get_by_fingerprint(fingerprint)

def is_ssh_key_already_registered(client, ssh_pub_key):
    return fetch_ssh_key_object_for_pub_key(client, ssh_pub_key) != None

def register_ssh_pub_key(client, ssh_pub_key):
    client.ssh_keys.create("Patrick SSH Key", ssh_pub_key, {})


def create_server(client, name, server_type, image, ssh_pub_key):
    ssh_key = fetch_ssh_key_object_for_pub_key(client, ssh_pub_key)
    response = client.servers.create(
        name=name,
        server_type=ServerType(name=server_type),
        image=Image(name=image),
        ssh_keys=[ssh_key]
    )

main()
