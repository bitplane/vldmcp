"""Server management commands for vldmcp - thin CLI layer."""

import click

from ..service.platform import get_platform
from ..service.system.config import set_platform_type
from ..models.config import PLATFORM_TYPES
from ..util.pprint import pprint_size
from ..util.output import output_nested_dict


@click.group()
def server():
    """Manage the vldmcp server."""
    pass


@server.command()
@click.option(
    "--platform",
    type=click.Choice([*PLATFORM_TYPES, "guess"], case_sensitive=False),
    default="guess",
    help="Platform to use for deployment (default: auto-detect)",
)
@click.option(
    "--recover",
    is_flag=True,
    help="Recover from existing seed phrase",
)
@click.option(
    "--show-seed",
    is_flag=True,
    help="Display seed phrase after generating new identity",
)
def install(platform, recover, show_seed):
    """Install base assets and prepare platform."""
    from .. import crypto

    click.echo("Setting up vldmcp...")

    # Set platform type if specified
    if platform != "guess":
        click.echo(f"Using {platform} platform")
        set_platform_type(platform)

    # Handle seed phrase recovery or generation
    platform = get_platform()
    user_key_path = platform.storage.user_key_path()

    if recover:
        # Recovery mode - prompt for seed phrase
        click.echo("\n🔑 Identity Recovery")
        click.echo("Enter your 24-word seed phrase (space-separated):")
        mnemonic = click.prompt("Seed phrase", hide_input=True, confirmation_prompt=True)

        # Validate and recover key
        try:
            if not crypto.is_valid_mnemonic(mnemonic):
                click.echo("❌ Invalid seed phrase. Please check your words and try again.")
                raise SystemExit(1)

            key = crypto.key_from_mnemonic(mnemonic)
            crypto.save_key(key, user_key_path)
            click.echo("✅ Identity recovered successfully!")

        except ValueError as e:
            click.echo(f"❌ Recovery failed: {e}")
            raise SystemExit(1)

    elif not user_key_path.exists():
        # New installation - generate new identity
        click.echo("\n🔑 Generating new identity...")
        mnemonic, key = crypto.generate_mnemonic_and_key()
        crypto.save_key(key, user_key_path)

        if show_seed:
            click.echo("\n⚠️  IMPORTANT: Write down your seed phrase!")
            click.echo("This is the ONLY way to recover your identity:\n")
            click.echo(f"  {mnemonic}\n")
            click.echo("Keep this phrase secure and never share it!")
            click.confirm("\nHave you written down your seed phrase?", abort=True)
        else:
            click.echo("✅ New identity created (use --show-seed to display recovery phrase)")
    else:
        # Existing installation
        click.echo("✅ Using existing identity")

    platform = get_platform()
    if platform.deploy():
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
    platform = get_platform()

    # Get list of what will be removed (for display)
    install_dir = platform.storage.install_dir()
    cache_dir = platform.storage.cache_dir()

    dirs_to_show = []
    # Always remove install and cache
    if install_dir.exists():
        dirs_to_show.append(("Install data", install_dir))
    if cache_dir.exists():
        dirs_to_show.append(("Cache", cache_dir))

    # --config flag: also remove config and state/runtime
    if config or purge:
        config_dir = platform.storage.config_dir()
        state_dir = platform.storage.state_dir()
        runtime_dir = platform.storage.runtime_dir()

        if config_dir.exists():
            dirs_to_show.append(("Configuration", config_dir))
        if state_dir.exists():
            dirs_to_show.append(("State data", state_dir))
        if runtime_dir.exists():
            dirs_to_show.append(("Runtime data", runtime_dir))

    # --purge flag: also remove user data (including keys)
    if purge:
        data_dir = platform.storage.data_dir()
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
    dirs_removed = platform.uninstall(config=config, purge=purge)

    for desc, path in dirs_removed:
        click.echo(f"Removed {desc}: {path}")

    click.echo("Uninstallation complete!")


@server.command()
def upgrade():
    """Upgrade vldmcp to latest version."""
    click.echo("Upgrading vldmcp...")

    platform = get_platform()
    if platform.upgrade():
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
    platform = get_platform()

    # Check if already running
    if platform.deploy_status() == "running":
        click.echo("Server is already running")
        return

    click.echo("Starting vldmcp server...")

    server_id = platform.deploy_start(debug=debug)
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

    platform = get_platform()
    if platform.deploy_stop():
        click.echo("Server stopped!")
    else:
        click.echo("No server running or failed to stop")
        raise SystemExit(1)


@server.command()
def export_seed():
    """Export the seed phrase for your identity."""
    from .. import crypto

    platform = get_platform()
    user_key_path = platform.storage.user_key_path()

    if not user_key_path.exists():
        click.echo("❌ No identity found. Run 'vldmcp server install' first.")
        raise SystemExit(1)

    click.echo("⚠️  This will display your seed phrase.")
    click.echo("Make sure no one is looking at your screen!")

    if not click.confirm("\nContinue?"):
        return

    try:
        key = crypto.load_key(user_key_path)
        if not key:
            click.echo("❌ Failed to load identity key.")
            raise SystemExit(1)

        mnemonic = crypto.mnemonic_from_key(key)

        click.echo("\n🔑 Your seed phrase (24 words):\n")
        click.echo(f"  {mnemonic}\n")
        click.echo("⚠️  Keep this phrase secure and never share it!")
        click.echo("This is the ONLY way to recover your identity.")

    except Exception as e:
        click.echo(f"❌ Failed to export seed phrase: {e}")
        raise SystemExit(1)


@server.command()
def logs():
    """View the server logs."""
    platform = get_platform()
    # Get PID from file and stream logs
    platform = get_platform()
    pid_file = platform.storage.pid_file_path()
    if not pid_file.exists():
        click.echo("Server not running")
        return

    pid_content = pid_file.read_text().strip()
    platform.stream_logs(pid_content)


@server.command()
@click.option("-h", "--human", is_flag=True, help="Output human-readable sizes instead of bytes")
def du(human):
    """Show disk usage for vldmcp."""
    platform = get_platform()

    # Get sizes in bytes from runtime
    usage = platform.du()

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
