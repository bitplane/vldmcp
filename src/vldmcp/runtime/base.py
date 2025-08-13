"""Abstract base class for runtime backends."""

import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from .. import paths, crypto
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

    def deploy(self) -> bool:
        """Deploy the runtime environment (calls install, then build if needed).

        Returns:
            True if deployment succeeded, False otherwise
        """
        if not self.install():
            return False
        return self.build_if_needed()

    def install(self) -> bool:
        """Install and set up the runtime environment.

        Returns:
            True if installation succeeded, False otherwise
        """
        # Create all XDG directories with proper permissions
        paths.create_directories()

        # Ensure user identity key exists
        crypto.ensure_user_key()

        # Ensure secure permissions
        paths.ensure_secure_permissions()

        return True

    def build_if_needed(self) -> bool:
        """Build if this runtime needs building (default: no build needed).

        Returns:
            True if build succeeded or not needed, False if build failed
        """
        return True  # Default: no build needed

    def uninstall(self, purge: bool = False) -> list[tuple[str, Path]]:
        """Uninstall the runtime environment.

        Args:
            purge: If True, also remove user keys and config

        Returns:
            List of (description, path) tuples that were removed
        """
        dirs_removed = []

        # Always remove install data and cache
        for desc, dir_path in [
            ("Install data", paths.install_dir()),
            ("Cache", paths.cache_dir()),
        ]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                dirs_removed.append((desc, dir_path))

        if purge:
            # Also remove keys, config, and state
            for desc, dir_path in [
                ("Configuration", paths.config_dir()),
                ("User data (including keys)", paths.data_dir()),
                ("State data", paths.state_dir()),
                ("Runtime data", paths.runtime_dir()),
            ]:
                if dir_path.exists():
                    shutil.rmtree(dir_path)
                    dirs_removed.append((desc, dir_path))

        return dirs_removed

    @abstractmethod
    def deploy_start(self, debug: bool = False) -> Optional[str]:
        """Deploy and start the server (runtime-specific implementation).

        Args:
            debug: If True, run in debug mode

        Returns:
            Server ID if started successfully, None if failed
        """
        pass

    @abstractmethod
    def deploy_stop(self) -> bool:
        """Stop the deployed server (runtime-specific implementation).

        Returns:
            True if stopped successfully, False otherwise
        """
        pass

    @abstractmethod
    def deploy_status(self) -> str:
        """Get status of deployed server (runtime-specific implementation).

        Returns:
            Status string ("running", "stopped", "not running", etc.)
        """
        pass
