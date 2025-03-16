#!/usr/bin/env python

import click
from providers import ServerProvider
from configuration import Configuration

@click.group()
def cli():
    pass

@cli.command()
@click.argument('file_name', type=click.Path(exists=True))
def deploy(file_name):
    config = Configuration.from_manifest(file_name)

    provider = ServerProvider(config)

    provider.provision_server()

if __name__ == '__main__':
    cli()
