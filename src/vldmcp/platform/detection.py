"""Platform detection and configuration for vldmcp deployments."""

import shutil

from ..util.version import is_development
from ..config import get_config, set_platform_type
from . import PlatformBackend, NativePlatform, PodmanPlatform
from ..models.config import PLATFORM_TYPES


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

    if shutil.which("podman"):
        return "podman"

    if shutil.which("vldmcpd"):
        return "native"

    # Default fallback - should rarely be reached
    return "native"


def get_platform(name: str = "guess") -> PlatformBackend:
    """Get a platform backend instance.

    Args:
        name: Platform name or "guess" to auto-detect

    Returns:
        PlatformBackend instance

    Raises:
        ValueError: If platform name is invalid
        RuntimeError: If auto-detection fails
    """
    # If name is "guess", check config first, then auto-detect
    if name == "guess":
        config = get_config()
        if config.platform.type == "guess":
            # Auto-detect and save
            detected_type = guess_platform()
            set_platform_type(detected_type)
            name = detected_type
        else:
            name = config.platform.type

    # Normalize name
    name = name.lower().strip()

    # Instantiate the platform
    if name == "native":
        return NativePlatform()
    elif name == "podman":
        return PodmanPlatform()
    else:
        raise ValueError(f"Unsupported platform '{name}'. " f"Valid options: {', '.join(sorted(PLATFORM_TYPES))}")
