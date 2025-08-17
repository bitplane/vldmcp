"""Command line interface for vldmcp."""

import click

from .. import __version__
from .lifecycle import server
from ..service.platform import get_platform
from ..models.info import InfoResponse, ServerInfo
from ..util.pprint import pprint_dict


@click.group()
@click.version_option(version=__version__, prog_name="vldmcp")
@click.pass_context
def cli(ctx):
    """vldmcp - A distributed (FoaF) MCP server using veilid and podman."""
    pass


# Add server subcommand group
cli.add_command(server)


@cli.command()
def info():
    """Show system information (client and server status)."""
    platform = get_platform()

    # Get client info
    client_info = platform.info()

    # Get server info (currently returns defaults until daemon is implemented)
    server_info = ServerInfo()

    # Combine into response
    response = InfoResponse(client=client_info, server=server_info)

    # Output as nested dict (similar to du command)
    response_dict = response.model_dump(exclude_none=True, exclude_defaults=False)
    pprint_dict(response_dict, output_func=click.echo, tab_separated=True, filter_empty=True)


if __name__ == "__main__":
    cli()
