"""vldmcp - A distributed (FoaF) MCP server using veilid and podman."""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("vldmcp")
except PackageNotFoundError:
    __version__ = "unknown"
