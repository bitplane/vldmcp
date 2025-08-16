"""File system service for vldmcp."""

from pathlib import Path
from .service import Service
from . import paths


class FileService(Service):
    """Service that manages file system access with permission control."""

    @classmethod
    def name(cls) -> str:
        return "files"

    def start(self):
        """Ensure directories exist on start."""
        paths.create_directories()
        paths.ensure_secure_permissions()
        self._running = True

    def stop(self):
        """Nothing to do on stop."""
        self._running = False

    # Directory accessors
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return paths.data_dir()

    def config_dir(self) -> Path:
        """Get the config directory path."""
        return paths.config_dir()

    def state_dir(self) -> Path:
        """Get the state directory path."""
        return paths.state_dir()

    def cache_dir(self) -> Path:
        """Get the cache directory path."""
        return paths.cache_dir()

    def runtime_dir(self) -> Path:
        """Get the runtime directory path."""
        return paths.runtime_dir()

    def install_dir(self) -> Path:
        """Get the install directory path."""
        return paths.install_dir()

    def repos_dir(self) -> Path:
        """Get the repositories directory path."""
        return paths.repos_dir()

    def www_dir(self) -> Path:
        """Get the www directory path."""
        return paths.www_dir()

    # File accessors
    def user_key_path(self) -> Path:
        """Get the user key file path."""
        return paths.user_key_path()

    def node_key_path(self, node_id: str) -> Path:
        """Get a node key file path."""
        return paths.node_key_path(node_id)

    def pid_file_path(self) -> Path:
        """Get the PID file path."""
        return paths.pid_file_path()

    # File operations (with permission checks in the future)
    def read_file(self, path: Path, context=None) -> bytes:
        """Read a file (with permission checks).

        Args:
            path: Path to read
            context: Security context for permission check

        Returns:
            File contents

        Raises:
            PermissionError: If access denied
            FileNotFoundError: If file doesn't exist
        """
        # TODO: Add permission checks based on context
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return path.read_bytes()

    def write_file(self, path: Path, content: bytes, context=None) -> None:
        """Write a file (with permission checks).

        Args:
            path: Path to write
            content: Content to write
            context: Security context for permission check

        Raises:
            PermissionError: If access denied
        """
        # TODO: Add permission checks based on context
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def read_text(self, path: Path, context=None) -> str:
        """Read a text file (with permission checks).

        Args:
            path: Path to read
            context: Security context for permission check

        Returns:
            File contents as string
        """
        return self.read_file(path, context).decode("utf-8")

    def write_text(self, path: Path, content: str, context=None) -> None:
        """Write a text file (with permission checks).

        Args:
            path: Path to write
            content: Content to write
            context: Security context for permission check
        """
        self.write_file(path, content.encode("utf-8"), context)

    def exists(self, path: Path) -> bool:
        """Check if a path exists."""
        return path.exists()

    def is_file(self, path: Path) -> bool:
        """Check if a path is a file."""
        return path.is_file()

    def is_dir(self, path: Path) -> bool:
        """Check if a path is a directory."""
        return path.is_dir()

    # Directory management
    def create_directories(self) -> None:
        """Create all required directories."""
        paths.create_directories()

    def ensure_secure_permissions(self) -> None:
        """Ensure secure permissions on sensitive directories."""
        paths.ensure_secure_permissions()
