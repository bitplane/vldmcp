"""Abstract base class for platform backends."""

import subprocess
from pathlib import Path

from .. import Service
from ..system.config import ConfigService
from ..system.storage import Storage
from ..system.crypto import CryptoService
from ...models.disk_usage import DiskUsage, InstallUsage, McpUsage
from ...models.info import ClientInfo


class Platform(Service):
    """Base class for different platforms (podman, native, etc).

    Platforms manage vldmcp deployment and execution.
    """

    def __init__(self):
        super().__init__()
        # Add core services that all platforms need
        storage = Storage()
        self.add_service(storage)
        self.add_service(ConfigService(storage))
        self.add_service(CryptoService())

    def build(self, force: bool = False) -> bool:
        """Build the platform environment.

        Args:
            force: Force rebuild even if already built

        Returns:
            True if build succeeded or not needed
        """
        return True

    def logs(self, server_id: str | None = None) -> str:
        """Get platform logs."""
        # Default implementation - platforms can override
        return "No logs available"

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
        config_size = get_dir_size(self.storage.config_dir()) + get_dir_size(self.storage.runtime_dir())

        # Install breakdown
        install_dir = self.storage.install_dir()
        install_image_size = get_dir_size(install_dir / "base") if install_dir.exists() else 0
        install_data_size = get_dir_size(self.storage.data_dir()) + get_dir_size(self.storage.state_dir())

        # MCP breakdown
        repos_size = get_dir_size(self.storage.repos_dir())
        mcp_images_size = 0  # Container backends will override this
        mcp_data_size = get_dir_size(self.storage.cache_dir())

        # WWW data
        www_size = get_dir_size(self.storage.www_dir())

        return DiskUsage(
            config=config_size,
            install=InstallUsage(image=install_image_size, data=install_data_size),
            mcp=McpUsage(repos=repos_size, images=mcp_images_size, data=mcp_data_size),
            www=www_size,
        )

    def deploy(self) -> bool:
        """Deploy and build the platform environment.

        Returns:
            True if deployment succeeded, False otherwise
        """
        # Create all XDG directories with proper permissions
        self.storage.create_directories()

        # Ensure user identity key exists
        crypto_service = self.get_service("crypto")
        crypto_service.ensure_user_key(self.storage)

        # Ensure secure permissions
        self.storage.ensure_secure_permissions()

        # Save config to establish deployment
        config_service = self.get_service("config")
        if config_service:
            config_service.save()

        # Build the platform
        return self.build()

    def start(self):
        """Start the platform services."""
        super().start()

    def stop(self):
        """Stop the platform services."""
        super().stop()

    def info(self) -> ClientInfo:
        """Get client-side information about the runtime.

        Returns:
            ClientInfo with current runtime status and configuration
        """
        # Get ports from config
        ports = []
        # TODO: Add ports to platform config model

        # Get server PID if running
        server_pid = None
        pid_file = self.storage.pid_file_path()
        if pid_file.exists():
            try:
                server_pid = pid_file.read_text().strip()
            except (OSError, ValueError):
                pass

        return ClientInfo(
            runtime_type=self.__class__.__name__.replace("Platform", "").lower(),
            server_status=self.status(),
            server_pid=server_pid,
            ports=ports,
        )

    def status(self) -> str:
        """Get platform status.

        Returns:
            Status string ("running", "stopped", "not deployed", etc.)
        """
        # Check if deployed (config exists)
        config_dir = self.storage.config_dir()
        if not config_dir.exists():
            return "not deployed"

        return "stopped"

    def remove(self, config: bool = False, purge: bool = False) -> list[tuple[str, Path]]:
        """Remove the platform environment.

        Args:
            config: If True, also remove config, state, and runtime dirs
            purge: If True, also remove user keys and all user data

        Returns:
            List of (description, path) tuples that were removed
        """
        import shutil

        dirs_removed = []

        # Always remove install and cache
        install_dir = self.storage.install_dir()
        if install_dir.exists():
            shutil.rmtree(install_dir)
            dirs_removed.append(("install data", install_dir))

        cache_dir = self.storage.cache_dir()
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            dirs_removed.append(("cache", cache_dir))

        # Config flag: also remove config and state
        if config or purge:
            config_dir = self.storage.config_dir()
            if config_dir.exists():
                shutil.rmtree(config_dir)
                dirs_removed.append(("configuration", config_dir))

            state_dir = self.storage.state_dir()
            if state_dir.exists():
                shutil.rmtree(state_dir)
                dirs_removed.append(("state data", state_dir))

            runtime_dir = self.storage.runtime_dir()
            if runtime_dir.exists():
                shutil.rmtree(runtime_dir)
                dirs_removed.append(("runtime data", runtime_dir))

        # Purge flag: also remove user data (including keys)
        if purge:
            data_dir = self.storage.data_dir()
            if data_dir.exists():
                shutil.rmtree(data_dir)
                dirs_removed.append(("user data", data_dir))

        return dirs_removed
