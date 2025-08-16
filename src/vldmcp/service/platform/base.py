"""Abstract base class for platform backends."""

import subprocess
from pathlib import Path

from ..base import Service
from ..system.config import ConfigService
from ..system.storage import Storage
from ..system.crypto import CryptoService
from ...models.disk_usage import DiskUsage, InstallUsage, McpUsage
from ...models.info import ClientInfo
from ...util.paths import Paths


class Platform(Service):
    """Base class for different platforms (podman, native, etc).

    Platforms manage vldmcp deployment and execution.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # Platform has empty path for invisible routing
        self.path = ""

        # Add core services that all platforms need
        storage = Storage(self)
        ConfigService(storage, self)
        CryptoService(self)

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
        config_size = get_dir_size(Paths.CONFIG) + get_dir_size(Paths.RUNTIME)

        # Install breakdown
        install_image_size = get_dir_size(Paths.INSTALL / "base") if Paths.INSTALL.exists() else 0
        install_data_size = get_dir_size(Paths.DATA) + get_dir_size(Paths.STATE)

        # MCP breakdown
        repos_size = get_dir_size(Paths.REPOS)
        mcp_images_size = 0  # Container backends will override this
        mcp_data_size = get_dir_size(Paths.CACHE)

        # WWW data
        www_size = get_dir_size(Paths.WWW)

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
        self.crypto.ensure_user_key(self.storage)

        # Ensure secure permissions
        self.storage.ensure_secure_permissions()

        # Save config to establish deployment
        config = self.config.get_config()
        self.config.save_config(config)

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
        if not Paths.CONFIG.exists():
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
        if Paths.INSTALL.exists():
            shutil.rmtree(Paths.INSTALL)
            dirs_removed.append(("install data", Paths.INSTALL))

        if Paths.CACHE.exists():
            shutil.rmtree(Paths.CACHE)
            dirs_removed.append(("cache", Paths.CACHE))

        # Config flag: also remove config and state
        if config or purge:
            if Paths.CONFIG.exists():
                shutil.rmtree(Paths.CONFIG)
                dirs_removed.append(("configuration", Paths.CONFIG))

            if Paths.STATE.exists():
                shutil.rmtree(Paths.STATE)
                dirs_removed.append(("state data", Paths.STATE))

            if Paths.RUNTIME.exists():
                shutil.rmtree(Paths.RUNTIME)
                dirs_removed.append(("runtime data", Paths.RUNTIME))

        # Purge flag: also remove user data (including keys)
        if purge:
            if Paths.DATA.exists():
                shutil.rmtree(Paths.DATA)
                dirs_removed.append(("user data", Paths.DATA))

        return dirs_removed
