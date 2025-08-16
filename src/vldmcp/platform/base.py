"""Abstract base class for platform backends."""

import subprocess
from abc import abstractmethod
from pathlib import Path

from .. import paths
from ..config import get_config
from ..service import Service
from ..installer import InstallerService
from ..config_service import ConfigService
from ..key_service import KeyService
from ..file_service import FileService
from ..daemon_service import DaemonService
from ..models.disk_usage import DiskUsage, InstallUsage, McpUsage
from ..models.info import ClientInfo


class PlatformBackend(Service):
    """Abstract base class for different platform backends (podman, docker, native, etc).

    Platforms are Services that manage the vldmcp installation and core services.
    """

    def __init__(self):
        super().__init__()
        # Add core services that all platforms need
        self.add_service(FileService())
        self.add_service(KeyService())
        self.add_service(ConfigService())
        self.add_service(InstallerService())
        self.add_service(DaemonService())

    @abstractmethod
    def build(self, dockerfile_path: Path) -> bool:
        """Build the server image/environment."""
        pass

    def logs(self) -> str:
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
        config_size = get_dir_size(paths.config_dir()) + get_dir_size(paths.runtime_dir())

        # Install breakdown
        install_dir = paths.install_dir()
        install_image_size = get_dir_size(install_dir / "base") if install_dir.exists() else 0
        install_data_size = get_dir_size(paths.data_dir()) + get_dir_size(paths.state_dir())

        # MCP breakdown
        repos_size = get_dir_size(paths.repos_dir())
        mcp_images_size = 0  # Container backends will override this
        mcp_data_size = get_dir_size(paths.cache_dir())

        # WWW data
        www_size = get_dir_size(paths.www_dir())

        return DiskUsage(
            config=config_size,
            install=InstallUsage(image=install_image_size, data=install_data_size),
            mcp=McpUsage(repos=repos_size, images=mcp_images_size, data=mcp_data_size),
            www=www_size,
        )

    def deploy(self) -> bool:
        """Deploy the platform environment (calls install, then build if needed).

        Returns:
            True if deployment succeeded, False otherwise
        """
        installer = self.get_service("installer")
        if not installer or not installer.install():
            return False
        return self.build_if_needed()

    def install(self) -> bool:
        """Install and set up the platform environment.

        Returns:
            True if installation succeeded, False otherwise
        """
        installer = self.get_service("installer")
        if installer:
            return installer.install()
        return False

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
        if hasattr(config.runtime, "ports"):
            ports = config.runtime.ports

        # Get server PID if running
        server_pid = None
        pid_file = paths.pid_file_path()
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

    def uninstall(self, config: bool = False, purge: bool = False) -> list[tuple[str, Path]]:
        """Uninstall the platform environment.

        Args:
            config: If True, also remove config, state, and runtime dirs
            purge: If True, also remove user keys and all user data

        Returns:
            List of (description, path) tuples that were removed
        """
        installer = self.get_service("installer")
        if installer:
            return installer.uninstall(config=config, purge=purge)
        return []
