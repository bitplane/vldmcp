"""Abstract base class for platform backends."""

import subprocess
from abc import abstractmethod
from pathlib import Path

from ..system.config import get_config
from .. import Service
from ..system.config import ConfigService
from ..system.key import KeyService
from ..system.storage import Storage
from ..system.daemon import DaemonService
from ..system.crypto import CryptoService
from ...models.disk_usage import DiskUsage, InstallUsage, McpUsage
from ...models.info import ClientInfo


class PlatformBackend(Service):
    """Abstract base class for different platform backends (podman, docker, native, etc).

    Platforms are Services that manage the vldmcp installation and core services.
    """

    def __init__(self):
        super().__init__()
        # Add core services that all platforms need
        self.add_service(Storage())
        self.add_service(KeyService())
        self.add_service(ConfigService())
        self.add_service(DaemonService())
        self.add_service(CryptoService())

    def build(self, dockerfile_path: Path) -> bool:
        """Build the server image/environment.

        Default implementation: no build needed.
        Override in subclasses that need building (e.g., container platforms).
        """
        return True

    def logs(self, server_id: str | None = None) -> str:
        """Get platform logs."""
        # Default implementation - platforms can override
        return "No logs available"

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
        """Deploy the platform environment (install and build if needed).

        Returns:
            True if deployment succeeded, False otherwise
        """
        # Create all XDG directories with proper permissions
        self.storage.create_directories()

        # Ensure user identity key exists
        from ... import crypto

        crypto.ensure_user_key(self.storage)

        # Ensure secure permissions
        self.storage.ensure_secure_permissions()

        # Build if needed (subclasses can override)
        return self.build_if_needed()

    def build_if_needed(self) -> bool:
        """Build if this runtime needs building (default: no build needed).

        Returns:
            True if build succeeded or not needed, False if build failed
        """
        return True  # Default: no build needed

    @abstractmethod
    def upgrade(self) -> bool:
        """Upgrade vldmcp to latest version (runtime-specific implementation).

        Returns:
            True if upgrade succeeded, False otherwise
        """
        pass

    def info(self) -> ClientInfo:
        """Get client-side information about the runtime.

        Returns:
            ClientInfo with current runtime status and configuration
        """
        config = get_config()

        # Get ports from config
        ports = []
        if hasattr(config.platform, "ports"):
            ports = config.platform.ports

        # Get server PID if running
        server_pid = None
        pid_file = self.storage.pid_file_path()
        if pid_file.exists():
            try:
                server_pid = pid_file.read_text().strip()
            except (OSError, ValueError):
                pass

        return ClientInfo(
            runtime_type=self.__class__.__name__.replace("Backend", "").lower(),
            server_status=self.deploy_status(),
            server_pid=server_pid,
            ports=ports,
        )

    def deploy_status(self) -> str:
        """Get deployment status (default implementation).

        Returns:
            Status string ("running", "stopped", "not running", etc.)
        """
        # Default implementation - platforms should override
        return "unknown"

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
