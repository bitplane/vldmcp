"""Server management commands for vldmcp - thin CLI layer."""

import click

from .. import paths
from ..runtime import get_runtime
from ..config import set_runtime_type
from ..models.config import RUNTIME_TYPES
from ..util.pprint import pprint_size
from ..util.output import output_nested_dict


@click.group()
def server():
    """Manage the vldmcp server."""
    pass


@server.command()
@click.option(
    "--runtime",
    type=click.Choice([*RUNTIME_TYPES, "guess"], case_sensitive=False),
    default="guess",
    help="Runtime to use for deployment (default: auto-detect)",
)
def install(runtime):
    """Install base assets and prepare runtime."""

    click.echo("Setting up vldmcp...")

    # Set runtime type if specified
    if runtime != "guess":
        click.echo(f"Using {runtime} runtime")
        set_runtime_type(runtime)

    runtime = get_runtime()
    if runtime.deploy():
        click.echo("Installation complete!")
    else:
        click.echo("Installation failed!")
        raise SystemExit(1)


@server.command()
@click.option(
    "--config",
    is_flag=True,
    help="Also remove configuration files",
)
@click.option(
    "--purge",
    is_flag=True,
    help="Remove everything including user keys and all user data",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def uninstall(config, purge, yes):
    """Uninstall the vldmcp server and optionally remove all user data."""
    runtime = get_runtime()

    # Get list of what will be removed (for display)
    install_dir = paths.install_dir()
    cache_dir = paths.cache_dir()

    dirs_to_show = []
    # Always remove install and cache
    if install_dir.exists():
        dirs_to_show.append(("Install data", install_dir))
    if cache_dir.exists():
        dirs_to_show.append(("Cache", cache_dir))

    # --config flag: also remove config and state/runtime
    if config or purge:
        config_dir = paths.config_dir()
        state_dir = paths.state_dir()
        runtime_dir = paths.runtime_dir()

        if config_dir.exists():
            dirs_to_show.append(("Configuration", config_dir))
        if state_dir.exists():
            dirs_to_show.append(("State data", state_dir))
        if runtime_dir.exists():
            dirs_to_show.append(("Runtime data", runtime_dir))

    # --purge flag: also remove user data (including keys)
    if purge:
        data_dir = paths.data_dir()
        if data_dir.exists():
            dirs_to_show.append(("User data (including keys)", data_dir))

    if not dirs_to_show:
        click.echo("No vldmcp installation found.")
        return

    # Show what will be removed
    click.echo("The following will be removed:")
    for desc, path in dirs_to_show:
        click.echo(f"  {desc}: {path}")

    if purge:
        click.echo("\n⚠️  WARNING: --purge will remove your identity keys!")
        click.echo("   This cannot be undone and will break connections to other nodes.")

    if not yes:
        click.confirm("\nContinue?", abort=True)

    # Do the actual removal
    dirs_removed = runtime.uninstall(config=config, purge=purge)

    for desc, path in dirs_removed:
        click.echo(f"Removed {desc}: {path}")

    click.echo("Uninstallation complete!")


@server.command()
def upgrade():
    """Upgrade vldmcp to latest version."""
    click.echo("Upgrading vldmcp...")

    runtime = get_runtime()
    if runtime.upgrade():
        click.echo("Upgrade complete!")
    else:
        click.echo("Upgrade failed!")
        raise SystemExit(1)


@server.command()
@click.option(
    "--debug",
    is_flag=True,
    help="Run server directly without container (for debugging)",
)
def start(debug):
    """Start the vldmcp server."""
    runtime = get_runtime()

    # Check if already running
    if runtime.deploy_status() == "running":
        click.echo("Server is already running")
        return

    click.echo("Starting vldmcp server...")

    server_id = runtime.deploy_start(debug=debug)
    if server_id:
        if debug:
            click.echo(f"Server started in debug mode (PID: {server_id})")
        else:
            click.echo(f"Server started! (PID: {server_id})")
    else:
        click.echo("Failed to start server")
        raise SystemExit(1)


@server.command()
def stop():
    """Stop the vldmcp server."""
    click.echo("Stopping vldmcp server...")

    runtime = get_runtime()
    if runtime.deploy_stop():
        click.echo("Server stopped!")
    else:
        click.echo("No server running or failed to stop")
        raise SystemExit(1)


@server.command()
def logs():
    """View the server logs."""
    runtime = get_runtime()
    # Get PID from file and stream logs
    pid_file = paths.pid_file_path()
    if not pid_file.exists():
        click.echo("Server not running")
        return

    pid_content = pid_file.read_text().strip()
    runtime.stream_logs(pid_content)


@server.command()
@click.option("-h", "--human", is_flag=True, help="Output human-readable sizes instead of bytes")
def du(human):
    """Show disk usage for vldmcp."""
    runtime = get_runtime()

    # Get sizes in bytes from runtime
    usage = runtime.du()

    # Convert to dict for processing
    usage_dict = usage.model_dump(exclude_none=True, exclude_defaults=False)

    # Convert to human readable if requested
    if human:
        usage_dict = _humanize_sizes(usage_dict)

    # Output as tab-separated
    output_nested_dict(usage_dict)


def _humanize_sizes(d):
    """Recursively convert byte sizes to human-readable format."""
    result = {}
    for key, value in d.items():
        if isinstance(value, dict):
            result[key] = _humanize_sizes(value)
        elif isinstance(value, int):
            result[key] = pprint_size(value)
        else:
            result[key] = value
    return result
