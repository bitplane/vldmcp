"""File system service for vldmcp."""

from pathlib import Path
from ..base import Service
from ...util.paths import Paths


class Storage(Service):
    """Service that manages file system access with permission control."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def start(self):
        """Ensure directories exist on start."""
        super().start()
        self.create_directories()
        self.ensure_secure_permissions()

    def stop(self):
        """Nothing to do on stop."""
        super().stop()

    # File accessors
    def user_key_path(self) -> Path:
        """Get the user key file path."""
        return Paths.KEYS / "user.key"

    def node_dir(self, node_id: str) -> Path:
        """Get the directory for a specific node's data."""
        return Paths.STATE / "nodes" / node_id

    def node_key_path(self, node_id: str) -> Path:
        """Get a node key file path."""
        return self.node_dir(node_id) / "key"

    def pid_file_path(self) -> Path:
        """Get the PID file path."""
        return Paths.RUNTIME / "vldmcp.pid"

    def database_path(self, name: str) -> Path:
        """Get path for a database file."""
        return Paths.STATE / f"{name}.db"

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
        # Create all base directories
        Paths.CONFIG.mkdir(parents=True, exist_ok=True)
        Paths.DATA.mkdir(parents=True, exist_ok=True)
        Paths.STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
        Paths.CACHE.mkdir(parents=True, exist_ok=True)
        Paths.RUNTIME.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Create derived directories
        Paths.KEYS.mkdir(parents=True, exist_ok=True, mode=0o700)
        Paths.INSTALL.mkdir(parents=True, exist_ok=True)
        Paths.REPOS.mkdir(parents=True, exist_ok=True)
        Paths.BUILD.mkdir(parents=True, exist_ok=True)

        # Create www directory and subdirectories
        Paths.WWW.mkdir(parents=True, exist_ok=True)
        (Paths.WWW / "models").mkdir(exist_ok=True)
        (Paths.WWW / "assets").mkdir(exist_ok=True)
        (Paths.WWW / "uploads").mkdir(exist_ok=True)
        (Paths.WWW / "generated").mkdir(exist_ok=True)

    def ensure_secure_permissions(self) -> None:
        """Ensure all sensitive directories and files have correct permissions."""
        # Secure the keys directory
        if Paths.KEYS.exists():
            Paths.KEYS.chmod(0o700)

            # Secure the user key file if it exists
            user_key = self.user_key_path()
            if user_key.exists():
                user_key.chmod(0o600)

        # Secure the state directory
        if Paths.STATE.exists():
            Paths.STATE.chmod(0o700)

            # Secure all node directories and key files
            nodes_dir = Paths.STATE / "nodes"
            if nodes_dir.exists():
                for node_path in nodes_dir.iterdir():
                    if node_path.is_dir():
                        node_path.chmod(0o700)
                        key_file = node_path / "key"
                        if key_file.exists():
                            key_file.chmod(0o600)

        # Secure the runtime directory
        if Paths.RUNTIME.exists():
            Paths.RUNTIME.chmod(0o700)
