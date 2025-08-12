"""Command line interface for vldmcp."""

import os
import shutil
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
    """Deploy the Docker base image and optionally clone the git repo."""
    prefix_path = Path(prefix)
    vldmcp_dir = prefix_path / "vldmcp"
    base_dir = vldmcp_dir / "base"

    # Create directories
    base_dir.mkdir(parents=True, exist_ok=True)

    # Find Dockerfile in our package
    package_root = Path(__file__).parent
    dockerfile_src = package_root.parent.parent / "Dockerfile"

    if not dockerfile_src.exists():
        # Try to find it relative to the installed package
        import vldmcp

        module_path = Path(vldmcp.__file__).parent
        dockerfile_src = module_path / "Dockerfile"

    if dockerfile_src.exists():
        # Copy Dockerfile to deployment location
        shutil.copy2(dockerfile_src, base_dir / "Dockerfile")
        click.echo(f"Copied Dockerfile to {base_dir}")
    else:
        click.echo("Warning: Could not find Dockerfile", err=True)

    # If this is a release version (no + in version), clone the repo
    if "+" not in __version__ and __version__ != "unknown":
        repo_dir = vldmcp_dir / "repo"
        if not repo_dir.exists():
            click.echo("Cloning vldmcp repository...")
            subprocess.run(["git", "clone", "https://github.com/bitplane/vldmcp.git", str(repo_dir)], check=True)
            click.echo(f"Repository cloned to {repo_dir}")
        else:
            click.echo(f"Repository already exists at {repo_dir}")
    else:
        click.echo(f"Development version detected ({__version__}), skipping repo clone")

    click.echo("Deployment complete!")


if __name__ == "__main__":
    cli()
