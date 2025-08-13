"""Server management commands for vldmcp - thin CLI layer."""

import subprocess

import click

from .. import paths
from ..server_manager import ServerManager


@click.group()
def server():
    """Manage the vldmcp server."""
    pass


@server.command()
def install():
    """Install the Docker base image and setup vldmcp."""
    click.echo("Setting up vldmcp...")

    manager = ServerManager()
    if manager.install():
        click.echo("Installation complete!")
    else:
        click.echo("Installation failed!")
        raise click.Exit(1)


@server.command()
@click.option(
    "--purge",
    is_flag=True,
    help="Also remove user keys, config, and all user data",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def uninstall(purge, yes):
    """Uninstall the vldmcp server and optionally remove all user data."""
    manager = ServerManager()

    # Get list of what will be removed (for display)
    install_dir = paths.install_dir()
    cache_dir = paths.cache_dir()

    dirs_to_show = []
    if install_dir.exists():
        dirs_to_show.append(("Install data", install_dir))
    if cache_dir.exists():
        dirs_to_show.append(("Cache", cache_dir))

    if purge:
        config_dir = paths.config_dir()
        data_dir = paths.data_dir()
        state_dir = paths.state_dir()
        runtime_dir = paths.runtime_dir()

        if config_dir.exists():
            dirs_to_show.append(("Configuration", config_dir))
        if data_dir.exists():
            dirs_to_show.append(("User data (including keys)", data_dir))
        if state_dir.exists():
            dirs_to_show.append(("State data", state_dir))
        if runtime_dir.exists():
            dirs_to_show.append(("Runtime data", runtime_dir))

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
    dirs_removed = manager.uninstall(purge=purge)

    for desc, path in dirs_removed:
        click.echo(f"Removed {desc.lower()}: {path}")

    click.echo("Uninstallation complete!")


@server.command()
def build():
    """Build the server container."""
    click.echo("Building server container...")

    manager = ServerManager()
    if manager.build():
        click.echo("Build complete!")
    else:
        click.echo("No installation found. Run 'vldmcp server install' first.")
        raise click.Exit(1)


@server.command()
@click.option(
    "--debug",
    is_flag=True,
    help="Run server directly without container (for debugging)",
)
def start(debug):
    """Start the vldmcp server."""
    manager = ServerManager()

    # Check if already running
    if manager.status() == "running":
        click.echo("Server is already running")
        return

    click.echo("Starting vldmcp server...")

    server_id = manager.start(debug=debug)
    if server_id:
        if debug:
            click.echo(f"Server started in debug mode (PID: {server_id})")
        else:
            click.echo("Server started!")
    else:
        click.echo("Failed to start server")
        raise click.Exit(1)


@server.command()
def stop():
    """Stop the vldmcp server."""
    click.echo("Stopping vldmcp server...")

    manager = ServerManager()
    if manager.stop():
        click.echo("Server stopped!")
    else:
        click.echo("No server running or failed to stop")
        raise click.Exit(1)


@server.command()
def status():
    """Check the status of the vldmcp server."""
    manager = ServerManager()
    status = manager.status()

    if status == "running":
        click.echo("Server is running")
    elif status == "stopped":
        click.echo("Server is stopped")
    else:
        click.echo("Server is not running")


@server.command()
def logs():
    """View the server logs."""
    manager = ServerManager()

    # For now, if using podman, stream logs directly
    # In future, manager.logs() could handle this better
    pid_file = paths.pid_file_path()
    if pid_file.exists() and "container:" in pid_file.read_text():
        subprocess.run(["podman", "logs", "-f", "vldmcp-server"], check=True)
    else:
        logs = manager.logs()
        click.echo(logs)


@server.command()
def du():
    """Show disk usage for vldmcp."""
    # Collect all vldmcp directories
    dirs_to_check = [
        ("Config", paths.config_dir()),
        ("Data", paths.data_dir()),
        ("State", paths.state_dir()),
        ("Cache", paths.cache_dir()),
        ("Install", paths.install_dir()),
        ("Runtime", paths.runtime_dir()),
    ]

    total_size = 0
    existing_dirs = []

    for desc, path in dirs_to_check:
        if path.exists():
            result = subprocess.run(["du", "-sb", str(path)], capture_output=True, text=True, check=True)
            size_bytes = int(result.stdout.split()[0])
            total_size += size_bytes

            # Human readable size
            result_hr = subprocess.run(["du", "-sh", str(path)], capture_output=True, text=True, check=True)
            size_hr = result_hr.stdout.split()[0]

            existing_dirs.append((desc, path, size_hr))

    if not existing_dirs:
        click.echo("No vldmcp installation found.")
        return

    # Convert total to human readable
    result_total = subprocess.run(["numfmt", "--to=iec", str(total_size)], capture_output=True, text=True)
    total_hr = result_total.stdout.strip() if result_total.returncode == 0 else f"{total_size} bytes"

    click.echo(f"Total vldmcp disk usage: {total_hr}")
    click.echo("\nBreakdown:")
    for desc, path, size in existing_dirs:
        click.echo(f"  {desc:8} {size:>8} {path}")
