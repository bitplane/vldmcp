"""vldmcp - A distributed (FoaF) MCP server using veilid and podman."""

import subprocess
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError


def _get_git_version():
    """Get version from git if we're in a repo."""
    try:
        # Check if we're in a git repo
        # Handle both normal install and -e mode
        current_path = Path(__file__).parent

        # In -e mode, we might be in src/vldmcp within the repo
        # Check up to 3 levels for .git directory
        for _ in range(3):
            current_path = current_path.parent
            if (current_path / ".git").exists():
                repo_root = current_path
                break
        else:
            return None

        # Get current branch
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=True
        ).stdout.strip()

        # Get short commit hash
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=True
        ).stdout.strip()

        # Get base version from pyproject.toml or use 0.0.0
        base_version = "0.0.1"

        # Format as semver-compatible version
        if branch == "main" or branch == "master":
            return f"{base_version}+{commit}"
        else:
            # Clean branch name for semver compatibility
            clean_branch = branch.replace("/", "-").replace("_", "-")
            return f"{base_version}+{clean_branch}.{commit}"
    except Exception:
        return None


# Try git first, then installed package, then unknown
_git_version = _get_git_version()
if _git_version:
    __version__ = _git_version
else:
    try:
        __version__ = version("vldmcp")
    except PackageNotFoundError:
        __version__ = "unknown"
