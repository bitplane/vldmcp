"""Server management commands for vldmcp."""

import os
import shutil
import subprocess
from pathlib import Path

import click

from .. import __version__

# Get the local repository path
import vldmcp

LOCAL_REPO = Path(vldmcp.__file__).parent.parent


@click.group()
def server():
    """Manage the vldmcp server."""
    pass


@server.command()
@click.option(
    "--prefix",
    default=os.path.expanduser("~/.local"),
    help="Installation prefix (default: ~/.local)",
    type=click.Path(),
)
def install(prefix):
    """Install the Docker base image and setup installation method."""
    prefix_path = Path(prefix)
    vldmcp_dir = prefix_path / "vldmcp"
    base_dir = vldmcp_dir / "base"

    # Create directories
    base_dir.mkdir(parents=True, exist_ok=True)

    # Determine if this is a git version or pip version
    is_git_version = "+" in __version__ and __version__ != "unknown"

    # Create Dockerfile content based on installation method
    if is_git_version:
        # Git-based installation - clone repo
        repo_dir = vldmcp_dir / "repo"

        # Extract version tag/branch from version string
        # Format is either base_version+commit or base_version+branch.commit
        if "+" in __version__:
            base_version, git_ref = __version__.split("+", 1)
            if "." in git_ref:
                # branch.commit format
                branch, commit = git_ref.rsplit(".", 1)
                checkout_ref = branch
            else:
                # just commit (main/master branch)
                checkout_ref = git_ref

        # Use local repo if it exists, otherwise GitHub
        if (LOCAL_REPO / ".git").exists():
            source_repo = str(LOCAL_REPO)
            click.echo(f"Using local repository at {source_repo}")
        else:
            source_repo = "https://github.com/bitplane/vldmcp.git"
            click.echo("Using GitHub repository")

        if repo_dir.exists():
            click.echo("Updating existing repository...")
            subprocess.run(["git", "fetch", "--all"], cwd=repo_dir, check=True)
            subprocess.run(
                ["git", "-c", "advice.detachedHead=false", "checkout", checkout_ref], cwd=repo_dir, check=True
            )
            click.echo(f"Repository updated to {checkout_ref}")
        else:
            click.echo("Cloning vldmcp repository...")
            subprocess.run(["git", "clone", source_repo, str(repo_dir)], check=True)
            subprocess.run(
                ["git", "-c", "advice.detachedHead=false", "checkout", checkout_ref], cwd=repo_dir, check=True
            )
            click.echo(f"Repository cloned and checked out to {checkout_ref}")

        # Create Dockerfile for git installation
        dockerfile_content = f"""FROM python:3.10-slim

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy the repository
COPY repo /app

WORKDIR /app

# Install the package
RUN pip install -e .

# Version: {__version__}
CMD ["vldmcp"]
"""
    else:
        # PyPI installation
        version_spec = __version__ if __version__ != "unknown" else ""

        # Create empty repo dir for testing
        repo_dir = vldmcp_dir / "repo"
        repo_dir.mkdir(parents=True, exist_ok=True)

        # Create Dockerfile for pip installation
        dockerfile_content = f"""FROM python:3.10-slim

WORKDIR /app

# Install from PyPI
RUN pip install vldmcp{f'=={version_spec}' if version_spec else ''}

# Version: {__version__}
CMD ["vldmcp"]
"""

    # Write Dockerfile
    dockerfile_path = base_dir / "Dockerfile"
    dockerfile_path.write_text(dockerfile_content)
    click.echo(f"Created Dockerfile at {dockerfile_path}")

    click.echo("Installation complete!")


@server.command()
@click.option(
    "--prefix",
    default=os.path.expanduser("~/.local"),
    help="Installation prefix (default: ~/.local)",
    type=click.Path(),
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt",
)
def uninstall(prefix, yes):
    """Uninstall the vldmcp server and remove all data."""
    prefix_path = Path(prefix)
    vldmcp_dir = prefix_path / "vldmcp"

    if not vldmcp_dir.exists():
        click.echo("No vldmcp installation found.")
        return

    if not yes:
        click.confirm(f"This will remove {vldmcp_dir} and all its contents. Continue?", abort=True)

    shutil.rmtree(vldmcp_dir)
    click.echo("Uninstallation complete!")


@server.command()
@click.option(
    "--prefix",
    default=os.path.expanduser("~/.local"),
    help="Installation prefix (default: ~/.local)",
    type=click.Path(),
)
def build(prefix):
    """Build the server container."""
    prefix_path = Path(prefix)
    base_dir = prefix_path / "vldmcp" / "base"

    if not base_dir.exists():
        click.echo("No installation found. Run 'vldmcp server install' first.")
        return

    click.echo("Building server container...")
    subprocess.run(["podman", "build", "-t", "vldmcp:latest", str(base_dir)], check=True)
    click.echo("Build complete!")


@server.command()
def start():
    """Start the vldmcp server."""
    click.echo("Starting vldmcp server...")
    subprocess.run(
        [
            "podman",
            "run",
            "-d",
            "--name",
            "vldmcp-server",
            "-p",
            "8080:8080",
            "-p",
            "8000:8000",
            "vldmcp:latest",
        ],
        check=True,
    )
    click.echo("Server started!")


@server.command()
def stop():
    """Stop the vldmcp server."""
    click.echo("Stopping vldmcp server...")
    subprocess.run(["podman", "stop", "vldmcp-server"], check=True)
    subprocess.run(["podman", "rm", "vldmcp-server"], check=True)
    click.echo("Server stopped!")


@server.command()
def status():
    """Check the status of the vldmcp server."""
    result = subprocess.run(["podman", "ps", "-a", "--filter", "name=vldmcp-server"], capture_output=True, text=True)
    if "vldmcp-server" in result.stdout:
        if "Up" in result.stdout:
            click.echo("Server is running")
        else:
            click.echo("Server is stopped")
    else:
        click.echo("Server is not installed")


@server.command()
def logs():
    """View the server logs."""
    subprocess.run(["podman", "logs", "-f", "vldmcp-server"], check=True)


@server.command()
@click.option(
    "--prefix",
    default=os.path.expanduser("~/.local"),
    help="Installation prefix (default: ~/.local)",
    type=click.Path(),
)
def du(prefix):
    """Show disk usage for vldmcp."""
    prefix_path = Path(prefix)
    vldmcp_dir = prefix_path / "vldmcp"

    if not vldmcp_dir.exists():
        click.echo("No vldmcp installation found.")
        return

    result = subprocess.run(["du", "-sh", str(vldmcp_dir)], capture_output=True, text=True, check=True)
    click.echo(result.stdout.strip())

    # Show breakdown
    click.echo("\nBreakdown:")
    subprocess.run(["du", "-sh", str(vldmcp_dir / "*")], shell=True, check=True)
