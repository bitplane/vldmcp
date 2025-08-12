"""Command line interface for vldmcp."""

import click

from .. import __version__
from .server import server


@click.group()
@click.version_option(version=__version__, prog_name="vldmcp")
@click.pass_context
def cli(ctx):
    """vldmcp - A distributed (FoaF) MCP server using veilid and podman."""
    pass


# Add server subcommand group
cli.add_command(server)


if __name__ == "__main__":
    cli()
