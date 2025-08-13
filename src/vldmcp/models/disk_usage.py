"""Disk usage models for vldmcp."""

from pydantic import BaseModel, Field


class InstallUsage(BaseModel):
    """Installation disk usage."""

    image: int | str = Field(default=0, description="Size of base image built from repo")
    data: int | str = Field(default=0, description="Size of installation data/volumes")


class McpUsage(BaseModel):
    """MCP services disk usage."""

    repos: int | str = Field(default=0, description="Size of downloaded MCP repos")
    images: int | str = Field(default=0, description="Size of MCP container images")
    data: int | str = Field(default=0, description="Size of MCP data/volumes")


class DiskUsage(BaseModel):
    """Disk usage information by functional area.

    All sizes are in bytes when human=False, or human-readable strings when human=True.
    """

    config: int | str = Field(default=0, description="Configuration and pid files")
    install: InstallUsage = Field(default_factory=InstallUsage, description="Installation usage")
    mcp: McpUsage = Field(default_factory=McpUsage, description="MCP services usage")
    www: int | str = Field(default=0, description="Static files, models, and uploaded content")

    @property
    def total(self) -> int | str:
        """Calculate total disk usage."""
        if isinstance(self.config, str):
            # Human-readable mode, can't calculate total easily
            return "N/A"

        total = (
            self.config
            + self.install.image
            + self.install.data
            + self.mcp.repos
            + self.mcp.images
            + self.mcp.data
            + self.www
        )
        return total
