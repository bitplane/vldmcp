"""Platform configuration models."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


# Single source of truth for platform types
PLATFORM_TYPES = ["native", "podman"]
PlatformType = Literal["native", "podman"]


class PlatformConfig(BaseModel):
    """Base platform configuration."""

    type: PlatformType | Literal["guess"] = "guess"


class NativeConfig(PlatformConfig):
    """Native process platform configuration."""

    type: Literal["native"] = "native"
    log_file: Path | None = Field(default=None, description="Path to log file for native daemon process")


class PodmanConfig(PlatformConfig):
    """Podman container platform configuration."""

    type: Literal["podman"] = "podman"
    image_name: str = Field(default="vldmcp:latest", description="Container image name to use")
    container_name: str = Field(default="vldmcp-server", description="Container name for the running instance")
    ports: list[str] = Field(default=["8080:8080", "8000:8000"], description="Port mappings (host:container)")
