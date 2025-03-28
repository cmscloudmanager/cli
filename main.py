#!/usr/bin/env python

import click
from server_providers import ServerProvider
from dns_providers import DnsProvider
from configuration import Configuration

from prepare_server_and_run_ansible import Server 

@click.group()
def cli():
    pass

@cli.command()
@click.argument('file_name', type=click.Path(exists=True))
def deploy(file_name):
    config = Configuration.from_manifest(file_name)

    server_provider = ServerProvider(config)

    server_info = server_provider.fetch_provisioned_server()
    if server_info != None:
        click.echo(f"Server {server_info.ipv4} ({server_info.ipv6}) already provisioned")
    else:
        click.echo(f"Provisioning server...")
        server_info = server_provider.provision_server()
        click.echo(f"Server {server_info.ipv4} ({server_info.ipv6}) successfully provisioned")

    config.render_ansible_vars()

    dns_provider = DnsProvider(config, server_info)
    dns_provider.render_dns_config()

    s = Server(server_info.ipv4)
    s.prepare_server_and_run_ansible()

    print(f"Server {server_info.ipv4} ({server_info.ipv6}) is now set up")

    print("Setting up DNS")
    s.run_dnscontrol()

    hostnames = dns_provider.get_hostnames()
    for hostname in hostnames:
        print(f"Waiting for DNS update for {hostname}")
        s.wait_for_dns(hostname, [server_info.ipv4, server_info.ipv6])

    print(f"DNS record successfully updated")

    print(f"Restarting services")
    s.restart_reverse_proxy()

    print(f"\n-----\n")
    print(f"ServeInfo:")
    print(f"  IPv4: {server_info.ipv4}")
    print(f"  IPv6: {server_info.ipv6}")
    print(f"")
    print(f"Deployed Web Apps:")
    for hostname in hostnames:
        print(f"  https://{hostname}")

if __name__ == '__main__':
    cli()
