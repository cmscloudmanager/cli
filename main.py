#!/usr/bin/env python

import click
from providers import ServerProvider
from configuration import Configuration

from prepare_server_and_run_ansible import Server 

@click.group()
def cli():
    pass

@cli.command()
@click.argument('file_name', type=click.Path(exists=True))
def deploy(file_name):
    config = Configuration.from_manifest(file_name)

    provider = ServerProvider(config)

    ip = provider.provision_server()

    server = Server(ip)
    server.prepare_server_and_run_ansible()

if __name__ == '__main__':
    cli()
