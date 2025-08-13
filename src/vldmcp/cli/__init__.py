"""Command line interface for vldmcp."""

import click

from .. import __version__
from .lifecycle import server
from ..runtime import get_runtime
from ..models.info import InfoResponse, ServerInfo


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
    runtime = get_runtime()

    # Get client info
    client_info = runtime.info()

    # Get server info (currently returns defaults until daemon is implemented)
    server_info = ServerInfo()

    # Combine into response
    response = InfoResponse(client=client_info, server=server_info)

    # Output as nested dict (similar to du command)
    response_dict = response.model_dump(exclude_none=True, exclude_defaults=False)
    _output_nested_dict(response_dict)


def _output_nested_dict(d, prefix=""):
    """Output nested dictionary in tab-separated format."""
    for key, value in d.items():
        if isinstance(value, dict):
            # Nested dict - recurse with prefix
            new_prefix = f"{prefix}.{key}" if prefix else key
            _output_nested_dict(value, new_prefix)
        else:
            # Leaf value - output as tab-separated
            full_key = f"{prefix}.{key}" if prefix else key
            if value and value != 0 and value != "0B":
                click.echo(f"{full_key}\t{value}")


if __name__ == "__main__":
    cli()
