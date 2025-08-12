"""Command line interface for vldmcp."""

import os
import subprocess
from pathlib import Path

import click

from . import __version__


@click.group()
@click.version_option(version=__version__, prog_name="vldmcp")
@click.pass_context
def cli(ctx):
    """vldmcp - A distributed (FoaF) MCP server using veilid and podman."""
    pass


@cli.command()
@click.option(
    "--prefix",
    default=os.path.expanduser("~/.local"),
    help="Installation prefix (default: ~/.local)",
    type=click.Path(),
)
def deploy(prefix):
    """Deploy the Docker base image and setup installation method."""
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

        if repo_dir.exists():
            click.echo("Updating existing repository...")
            subprocess.run(["git", "fetch", "--all"], cwd=repo_dir, check=True)
            subprocess.run(["git", "checkout", checkout_ref], cwd=repo_dir, check=True)
            click.echo(f"Repository updated to {checkout_ref}")
        else:
            click.echo("Cloning vldmcp repository...")
            subprocess.run(["git", "clone", "https://github.com/bitplane/vldmcp.git", str(repo_dir)], check=True)
            subprocess.run(["git", "checkout", checkout_ref], cwd=repo_dir, check=True)
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

    click.echo("Deployment complete!")


if __name__ == "__main__":
    cli()
