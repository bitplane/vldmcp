"""Platform backends for deploying vldmcp servers across different environments."""

from .base import Platform
from .podman import PodmanPlatform
from .native import NativePlatform
from .detection import get_platform, guess_platform

__all__ = ["Platform", "PodmanPlatform", "NativePlatform", "get_platform", "guess_platform"]
