"""Platform detection and configuration for vldmcp deployments."""

import shutil

from ...util.version import is_development
from . import Platform, NativePlatform

try:
    from . import PodmanPlatform
except ImportError:
    PodmanPlatform = None
from ...models.config import PLATFORM_TYPES


def guess_platform() -> str:
    """Guess the best platform based on environment and available tools.

    Priority order:
    1. If running from git repo, use native (for development)
    2. If podman available, use podman (preferred deployment)
    3. If vldmcpd available, use native (fallback)

    Returns:
        Platform name as string (e.g., "native", "podman")
    """
    if is_development():
        return "native"

    if PodmanPlatform is not None and shutil.which("podman"):
        return "podman"

    if shutil.which("vldmcpd"):
        return "native"

    # Default fallback - should rarely be reached
    return "native"


def get_platform(name: str = "guess") -> Platform:
    """Get a platform backend instance.

    Args:
        name: Platform name or "guess" to auto-detect

    Returns:
        Platform instance

    Raises:
        ValueError: If platform name is invalid
        RuntimeError: If auto-detection fails
    """
    # If name is "guess", auto-detect
    if name == "guess":
        name = guess_platform()

    # Normalize name
    name = name.lower().strip()

    # Instantiate the platform
    if name == "native":
        return NativePlatform()
    elif name == "podman":
        if PodmanPlatform is None:
            raise RuntimeError("Podman platform is not available. Use 'native' platform instead.")
        return PodmanPlatform()
    else:
        raise ValueError(f"Unsupported platform '{name}'. " f"Valid options: {', '.join(sorted(PLATFORM_TYPES))}")
