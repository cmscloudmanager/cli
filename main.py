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

    click.echo
    ip = provider.fetch_provisioned_server_ip()
    if ip != None:
        click.echo(f"Server {ip} already provisioned")
    else:
        click.echo(f"Provisioning server...")
        ip = provider.provision_server()
        click.echo(f"Server {ip} successfully provisioned")

    s = Server(ip)
    s.prepare_server_and_run_ansible()

if __name__ == '__main__':
    cli()
