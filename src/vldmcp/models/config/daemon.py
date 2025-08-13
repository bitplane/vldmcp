"""Daemon configuration models."""

from typing import Literal

from pydantic import BaseModel, Field


class DaemonConfig(BaseModel):
    """Daemon process configuration."""

    host: str = Field(default="localhost", description="Host to bind the daemon to")
    port: int = Field(default=8080, ge=1, le=65535, description="Port to bind the daemon to")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level for the daemon"
    )
    workers: int = Field(default=1, ge=1, description="Number of worker processes")
