"""Models for system information reporting."""

from typing import Optional

from pydantic import BaseModel, Field

from .. import __version__


class ClientInfo(BaseModel):
    """Information that the client knows about the system."""

    client_version: str = Field(default=__version__, description="Client version")
    runtime_type: str = Field(description="Runtime backend type (native, podman)")
    server_status: str = Field(description="Server running status")
    server_pid: Optional[str] = Field(default=None, description="Server process ID (if running)")
    ports: list[str] = Field(default_factory=list, description="Configured server ports")


class ServerInfo(BaseModel):
    """Information reported by the server (extensible for future features)."""

    server_version: Optional[str] = Field(default=None, description="Server version")
    server_pid: Optional[int] = Field(default=None, description="Server internal process ID")
    veilid_status: Optional[str] = Field(default=None, description="Veilid connection status")
    peer_count: Optional[int] = Field(default=None, description="Number of connected peers")
    tool_count: Optional[int] = Field(default=None, description="Number of available tools")


class InfoResponse(BaseModel):
    """Combined client and server information response."""

    client: ClientInfo = Field(description="Client-side information")
    server: ServerInfo = Field(description="Server-side information")
