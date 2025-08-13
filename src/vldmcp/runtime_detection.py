"""Runtime detection and configuration for vldmcp deployments."""

import subprocess

from . import __version__
from .config import get_config, set_runtime_type
from .runtime import RuntimeBackend, NativeBackend, PodmanBackend
from .models.config import RUNTIME_TYPES


def is_git_development() -> bool:
    """Check if we're running from a git development environment."""
    return "+" in __version__ and __version__ != "unknown"


def has_command(cmd: str) -> bool:
    """Check if a command is available in PATH."""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def guess_runtime() -> str:
    """Guess the best runtime based on environment and available tools.

    Priority order:
    1. If running from git repo, use native (for development)
    2. If podman available, use podman
    3. Raise RuntimeError if nothing available

    Returns:
        Runtime name as string (e.g., "native", "podman")

    Raises:
        RuntimeError: If no suitable runtime is found
    """
    if is_git_development():
        return "native"

    if has_command("podman"):
        return "podman"

    raise RuntimeError("No suitable runtime found. Please install podman or run from a development environment.")


def get_runtime(name: str = "guess") -> RuntimeBackend:
    """Get a runtime backend instance.

    Args:
        name: Runtime name or "guess" to auto-detect

    Returns:
        RuntimeBackend instance

    Raises:
        ValueError: If runtime name is invalid
        RuntimeError: If auto-detection fails
    """
    # If name is "guess", check config first, then auto-detect
    if name == "guess":
        config = get_config()
        if config.runtime.type == "guess":
            # Auto-detect and save
            detected_type = guess_runtime()
            set_runtime_type(detected_type)
            name = detected_type
        else:
            name = config.runtime.type

    # Normalize name
    name = name.lower().strip()

    # Instantiate the runtime
    if name == "native":
        return NativeBackend()
    elif name == "podman":
        return PodmanBackend()
    else:
        raise ValueError(f"Unsupported runtime '{name}'. " f"Valid options: {', '.join(sorted(RUNTIME_TYPES))}")
