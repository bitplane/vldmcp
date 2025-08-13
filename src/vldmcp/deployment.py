"""Server deployment and lifecycle management.

This module handles server installation, building, and lifecycle operations.
It coordinates with runtime backends for actual server execution.
"""

import os
from pathlib import Path
from typing import Optional

from . import __version__
from . import paths
from . import crypto
from .models.disk_usage import DiskUsage
from .runtime_detection import get_runtime
from .runtime import NativeBackend


class Deployment:
    """High-level server deployment and lifecycle management."""

    def __init__(self):
        """Initialize with runtime from configuration."""
        self.backend = get_runtime()

    def install(self) -> bool:
        """Install vldmcp with all necessary setup."""
        # Create all XDG directories with proper permissions
        paths.create_directories()

        # Ensure user identity key exists
        crypto.ensure_user_key()

        # Ensure secure permissions
        paths.ensure_secure_permissions()

        # Set up install directory for container assets
        install_dir = paths.install_dir()
        base_dir = install_dir / "base"
        base_dir.mkdir(parents=True, exist_ok=True)

        # Create appropriate Dockerfile/setup based on version
        self._create_dockerfile(base_dir)

        return True

    def _create_dockerfile(self, base_dir: Path) -> None:
        """Create Dockerfile for PyPI installation."""
        # Always use PyPI installation for containers
        version_spec = __version__ if __version__ != "unknown" else ""

        # Create Dockerfile
        dockerfile_content = f"""FROM python:3.10-slim

WORKDIR /app

# Install from PyPI
RUN pip install vldmcp{f'=={version_spec}' if version_spec else ''}

# Version: {__version__}
CMD ["vldmcpd"]
"""
        (base_dir / "Dockerfile").write_text(dockerfile_content)

    def uninstall(self, purge: bool = False) -> list[tuple[str, Path]]:
        """Uninstall vldmcp, optionally purging all data.

        Returns list of (description, path) tuples that were removed.
        """
        dirs_removed = []

        # Always remove install data and cache
        for desc, dir_path in [
            ("Install data", paths.install_dir()),
            ("Cache", paths.cache_dir()),
        ]:
            if dir_path.exists():
                import shutil

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
                    import shutil

                    shutil.rmtree(dir_path)
                    dirs_removed.append((desc, dir_path))

        return dirs_removed

    def build(self) -> bool:
        """Build the server container/environment."""
        base_dir = paths.install_dir() / "base"
        if not base_dir.exists():
            return False

        dockerfile = base_dir / "Dockerfile"
        if not dockerfile.exists():
            return False

        return self.backend.build(dockerfile)

    def start(self, debug: bool = False) -> Optional[str]:
        """Start the server, return server ID."""
        # Check if already running
        pid_file = paths.pid_file_path()
        if pid_file.exists():
            try:
                pid_content = pid_file.read_text().strip()
                # Check if still running
                if pid_content.startswith("container:"):
                    status = self.backend.status(pid_content)
                    if status == "running":
                        return None  # Already running
                else:
                    os.kill(int(pid_content), 0)
                    return None  # Already running
            except (OSError, ValueError):
                # Stale PID file, remove it
                pid_file.unlink()

        # Auto-install if needed
        if not paths.install_dir().exists() or not paths.user_key_path().exists():
            if not self.install():
                return None

        if debug or isinstance(self.backend, NativeBackend):
            # Run natively - use native backend for debug mode
            native_backend = NativeBackend()
            server_id = native_backend.start({}, [])
        else:
            # Ensure built
            if not self.build():
                return None

            # Create mount mappings
            mounts = {
                str(paths.state_dir()): "/var/lib/vldmcp:rw",
                str(paths.cache_dir()): "/var/cache/vldmcp:rw",
                str(paths.config_dir()): "/etc/vldmcp:ro",
                str(paths.runtime_dir()): "/run/vldmcp:rw",
            }

            # Start with backend
            server_id = self.backend.start(mounts, ["8080:8080", "8000:8000"])

        # Write PID file
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(server_id)

        return server_id

    def stop(self) -> bool:
        """Stop the server."""
        pid_file = paths.pid_file_path()

        if not pid_file.exists():
            return False

        pid_content = pid_file.read_text().strip()

        if pid_content.startswith("container:"):
            result = self.backend.stop(pid_content)
        else:
            result = self.backend.stop(pid_content)

        # Remove PID file
        if result:
            pid_file.unlink()

        return result

    def status(self) -> str:
        """Get server status."""
        pid_file = paths.pid_file_path()

        if not pid_file.exists():
            return "not running"

        pid_content = pid_file.read_text().strip()
        status = self.backend.status(pid_content)

        # Clean up stale PID file
        if status in ["stopped", "not found"]:
            pid_file.unlink()

        return status

    def logs(self) -> str:
        """Get server logs."""
        pid_file = paths.pid_file_path()

        if not pid_file.exists():
            return "Server not running"

        pid_content = pid_file.read_text().strip()
        return self.backend.logs(pid_content)

    def stream_logs(self) -> None:
        """Stream server logs to stdout."""
        pid_file = paths.pid_file_path()

        if not pid_file.exists():
            print("Server not running")
            return

        pid_content = pid_file.read_text().strip()
        self.backend.stream_logs(pid_content)

    def du(self) -> DiskUsage:
        """Get disk usage information from runtime backend.

        Returns:
            DiskUsage model with sizes in bytes by functional area
        """
        return self.backend.du()
