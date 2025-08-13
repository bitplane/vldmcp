"""Abstract base class for runtime backends."""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from ..models.disk_usage import DiskUsage, InstallUsage, McpUsage


class RuntimeBackend(ABC):
    """Abstract base class for different runtime backends (podman, docker, native, etc)."""

    @abstractmethod
    def build(self, dockerfile_path: Path) -> bool:
        """Build the server image/environment."""
        pass

    @abstractmethod
    def start(self, mounts: dict[str, str], ports: list[str]) -> str:
        """Start the server and return a process/container ID."""
        pass

    @abstractmethod
    def stop(self, server_id: str) -> bool:
        """Stop the server."""
        pass

    @abstractmethod
    def status(self, server_id: str) -> str:
        """Get server status."""
        pass

    @abstractmethod
    def logs(self, server_id: str) -> str:
        """Get server logs."""
        pass

    def stream_logs(self, server_id: str) -> None:
        """Stream server logs to stdout (default implementation prints static logs)."""
        logs = self.logs(server_id)
        print(logs)

    def du(self) -> DiskUsage:
        """Get disk usage information for this runtime.

        Returns:
            DiskUsage model with sizes in bytes by functional area
        """
        from .. import paths

        # Helper to get directory size in bytes
        def get_dir_size(path: Path) -> int:
            if not path.exists():
                return 0
            try:
                output = subprocess.run(["du", "-sb", str(path)], capture_output=True, text=True, check=True).stdout
                return int(output.split()[0])
            except (subprocess.CalledProcessError, ValueError):
                return 0

        # Calculate base sizes
        config_size = get_dir_size(paths.config_dir()) + get_dir_size(paths.runtime_dir())

        # Install breakdown
        install_dir = paths.install_dir()
        install_image_size = get_dir_size(install_dir / "base") if install_dir.exists() else 0
        install_data_size = get_dir_size(paths.data_dir()) + get_dir_size(paths.state_dir())

        # MCP breakdown
        repos_size = get_dir_size(paths.repos_dir())
        mcp_images_size = 0  # Container backends will override this
        mcp_data_size = get_dir_size(paths.cache_dir())

        return DiskUsage(
            config=config_size,
            install=InstallUsage(image=install_image_size, data=install_data_size),
            mcp=McpUsage(repos=repos_size, images=mcp_images_size, data=mcp_data_size),
        )
