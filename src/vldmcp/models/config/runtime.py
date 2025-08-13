"""Runtime configuration models."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


# Single source of truth for runtime types
RUNTIME_TYPES = ["native", "podman"]
RuntimeType = Literal["native", "podman"]


class RuntimeConfig(BaseModel):
    """Base runtime configuration."""

    type: RuntimeType | Literal["guess"] = "guess"


class NativeConfig(RuntimeConfig):
    """Native process runtime configuration."""

    type: Literal["native"] = "native"
    log_file: Path | None = Field(default=None, description="Path to log file for native daemon process")


class PodmanConfig(RuntimeConfig):
    """Podman container runtime configuration."""

    type: Literal["podman"] = "podman"
    image_name: str = Field(default="vldmcp:latest", description="Container image name to use")
    container_name: str = Field(default="vldmcp-server", description="Container name for the running instance")
    ports: list[str] = Field(default=["8080:8080", "8000:8000"], description="Port mappings (host:container)")
