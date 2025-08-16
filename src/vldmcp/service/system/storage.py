"""File system service for vldmcp."""

import os
from pathlib import Path
from .. import Service


class Storage(Service):
    """Service that manages file system access with permission control."""

    def start(self):
        """Ensure directories exist on start."""
        self.create_directories()
        self.ensure_secure_permissions()
        self._running = True

    def stop(self):
        """Nothing to do on stop."""
        self._running = False

    # Directory accessors
    def data_dir(self) -> Path:
        """Get the data directory path."""
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            return Path(xdg_data) / "vldmcp"
        return Path.home() / ".local" / "share" / "vldmcp"

    def config_dir(self) -> Path:
        """Get the config directory path."""
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "vldmcp"
        return Path.home() / ".config" / "vldmcp"

    def state_dir(self) -> Path:
        """Get the state directory path."""
        xdg_state = os.environ.get("XDG_STATE_HOME")
        if xdg_state:
            return Path(xdg_state) / "vldmcp"
        return Path.home() / ".local" / "state" / "vldmcp"

    def cache_dir(self) -> Path:
        """Get the cache directory path."""
        xdg_cache = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache:
            return Path(xdg_cache) / "vldmcp"
        return Path.home() / ".cache" / "vldmcp"

    def runtime_dir(self) -> Path:
        """Get the runtime directory path."""
        xdg_runtime = os.environ.get("XDG_RUNTIME_DIR")
        if xdg_runtime:
            return Path(xdg_runtime) / "vldmcp"
        user = os.environ.get("USER", "unknown")
        return Path(f"/tmp/vldmcp-{user}")

    def install_dir(self) -> Path:
        """Get the install directory path."""
        return self.data_dir() / "install"

    def repos_dir(self) -> Path:
        """Get the repositories directory path."""
        return self.cache_dir() / "src"

    def build_dir(self) -> Path:
        """Get the build directory path."""
        return self.cache_dir() / "build"

    def www_dir(self) -> Path:
        """Get the www directory path."""
        return self.data_dir() / "www"

    # File accessors
    def user_key_path(self) -> Path:
        """Get the user key file path."""
        return self.data_dir() / "keys" / "user.key"

    def node_dir(self, node_id: str) -> Path:
        """Get the directory for a specific node's data."""
        return self.state_dir() / "nodes" / node_id

    def node_key_path(self, node_id: str) -> Path:
        """Get a node key file path."""
        return self.node_dir(node_id) / "key"

    def pid_file_path(self) -> Path:
        """Get the PID file path."""
        return self.runtime_dir() / "vldmcp.pid"

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
        """Create all required directories with appropriate permissions."""
        # Create config directory
        self.config_dir().mkdir(parents=True, exist_ok=True)

        # Create data directory and keys subdirectory with secure permissions
        keys_dir = self.data_dir() / "keys"
        keys_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Create state directory with secure permissions
        self.state_dir().mkdir(parents=True, exist_ok=True, mode=0o700)

        # Create cache directories
        self.cache_dir().mkdir(parents=True, exist_ok=True)
        self.repos_dir().mkdir(parents=True, exist_ok=True)
        self.build_dir().mkdir(parents=True, exist_ok=True)

        # Create install directory
        self.install_dir().mkdir(parents=True, exist_ok=True)

        # Create www directory and subdirectories
        www = self.www_dir()
        www.mkdir(parents=True, exist_ok=True)
        (www / "models").mkdir(exist_ok=True)
        (www / "assets").mkdir(exist_ok=True)
        (www / "uploads").mkdir(exist_ok=True)
        (www / "generated").mkdir(exist_ok=True)

        # Create runtime directory with secure permissions
        self.runtime_dir().mkdir(parents=True, exist_ok=True, mode=0o700)

    def ensure_secure_permissions(self) -> None:
        """Ensure all sensitive directories and files have correct permissions."""
        # Secure the keys directory
        keys_dir = self.data_dir() / "keys"
        if keys_dir.exists():
            keys_dir.chmod(0o700)

            # Secure the user key file if it exists
            user_key = self.user_key_path()
            if user_key.exists():
                user_key.chmod(0o600)

        # Secure the state directory
        if self.state_dir().exists():
            self.state_dir().chmod(0o700)

            # Secure all node directories and key files
            nodes_dir = self.state_dir() / "nodes"
            if nodes_dir.exists():
                for node_path in nodes_dir.iterdir():
                    if node_path.is_dir():
                        node_path.chmod(0o700)
                        key_file = node_path / "key"
                        if key_file.exists():
                            key_file.chmod(0o600)

        # Secure the runtime directory
        if self.runtime_dir().exists():
            self.runtime_dir().chmod(0o700)
