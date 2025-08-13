"""Server management backend.

This module handles all server management operations independent of the CLI.
It abstracts away platform-specific details and container runtime choices.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple
from abc import ABC, abstractmethod

from . import __version__
from . import paths
from . import crypto


class RuntimeBackend(ABC):
    """Abstract base class for different runtime backends (podman, docker, native, etc)."""

    @abstractmethod
    def build(self, dockerfile_path: Path) -> bool:
        """Build the server image/environment."""
        pass

    @abstractmethod
    def start(self, mounts: dict[str, str], ports: List[str]) -> str:
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


class PodmanBackend(RuntimeBackend):
    """Podman container runtime backend."""

    def build(self, dockerfile_path: Path) -> bool:
        """Build container with podman."""
        result = subprocess.run(
            ["podman", "build", "-t", "vldmcp:latest", str(dockerfile_path.parent)], capture_output=True
        )
        return result.returncode == 0

    def start(self, mounts: dict[str, str], ports: List[str]) -> str:
        """Start container with podman."""
        cmd = ["podman", "run", "-d", "--name", "vldmcp-server"]

        # Add mounts
        for host_path, container_path in mounts.items():
            mode = "ro" if container_path.endswith(":ro") else "rw"
            container_path = container_path.replace(":ro", "").replace(":rw", "")
            cmd.extend(["-v", f"{host_path}:{container_path}:{mode}"])

        # Add ports
        for port in ports:
            cmd.extend(["-p", port])

        cmd.append("vldmcp:latest")

        subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Get container PID
        pid_result = subprocess.run(
            ["podman", "inspect", "--format", "{{.State.Pid}}", "vldmcp-server"],
            capture_output=True,
            text=True,
            check=True,
        )
        return f"container:{pid_result.stdout.strip()}"

    def stop(self, server_id: str) -> bool:
        """Stop podman container."""
        subprocess.run(["podman", "stop", "vldmcp-server"], check=True)
        subprocess.run(["podman", "rm", "vldmcp-server"], check=True)
        return True

    def status(self, server_id: str) -> str:
        """Check podman container status."""
        result = subprocess.run(
            ["podman", "ps", "-a", "--filter", "name=vldmcp-server"], capture_output=True, text=True
        )
        if "vldmcp-server" in result.stdout:
            if "Up" in result.stdout:
                return "running"
            else:
                return "stopped"
        return "not found"

    def logs(self, server_id: str) -> str:
        """Get podman container logs."""
        result = subprocess.run(["podman", "logs", "vldmcp-server"], capture_output=True, text=True)
        return result.stdout


class NativeBackend(RuntimeBackend):
    """Native process runtime backend (no container)."""

    def build(self, dockerfile_path: Path) -> bool:
        """No build needed for native."""
        return True

    def start(self, mounts: dict[str, str], ports: List[str]) -> str:
        """Start native server process."""
        # In a real implementation, this would start the actual server
        # For now, just return the current PID
        return str(os.getpid())

    def stop(self, server_id: str) -> bool:
        """Stop native server process."""
        try:
            pid = int(server_id)
            os.kill(pid, 15)  # SIGTERM
            return True
        except (ValueError, OSError):
            return False

    def status(self, server_id: str) -> str:
        """Check if native process is running."""
        try:
            pid = int(server_id)
            os.kill(pid, 0)
            return "running"
        except (ValueError, OSError):
            return "stopped"

    def logs(self, server_id: str) -> str:
        """Get native process logs."""
        # Would read from log file in real implementation
        return "Native process logs not yet implemented"


class ServerManager:
    """High-level server management interface."""

    def __init__(self, backend: Optional[RuntimeBackend] = None):
        """Initialize with a specific backend or auto-detect."""
        if backend is None:
            backend = self._detect_backend()
        self.backend = backend

    def _detect_backend(self) -> RuntimeBackend:
        """Auto-detect the best available backend."""
        # Check for podman
        try:
            subprocess.run(["podman", "--version"], capture_output=True, check=True)
            return PodmanBackend()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Check for docker
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            # Would return DockerBackend() if we had one
            pass
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        # Fall back to native
        return NativeBackend()

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
        """Create Dockerfile based on installation type."""
        # Determine if this is a git version or pip version
        is_git_version = "+" in __version__ and __version__ != "unknown"

        if is_git_version:
            # Git-based installation
            self._setup_git_install(base_dir, __version__)
        else:
            # PyPI installation
            self._setup_pip_install(base_dir, __version__)

    def _setup_git_install(self, base_dir: Path, version: str) -> None:
        """Set up git-based installation."""
        # Clone repo to cache
        repo_dir = paths.repos_dir() / "vldmcp"

        # Extract version info
        if "+" in version:
            base_version, git_ref = version.split("+", 1)
            if "." in git_ref:
                branch, commit = git_ref.rsplit(".", 1)
                checkout_ref = branch
            else:
                checkout_ref = git_ref

        # Clone or update repo
        if repo_dir.exists():
            subprocess.run(["git", "fetch", "--all"], cwd=repo_dir, check=True)
            subprocess.run(
                ["git", "-c", "advice.detachedHead=false", "checkout", checkout_ref], cwd=repo_dir, check=True
            )
        else:
            # Determine source repo
            import vldmcp

            local_repo = Path(vldmcp.__file__).parent.parent
            if (local_repo / ".git").exists():
                source_repo = str(local_repo)
            else:
                source_repo = "https://github.com/bitplane/vldmcp.git"

            subprocess.run(["git", "clone", source_repo, str(repo_dir)], check=True)
            subprocess.run(
                ["git", "-c", "advice.detachedHead=false", "checkout", checkout_ref], cwd=repo_dir, check=True
            )

        # Create Dockerfile
        dockerfile_content = f"""FROM python:3.10-slim

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy the repository
COPY repo /app

WORKDIR /app

# Install the package
RUN pip install -e .

# Version: {version}
CMD ["vldmcp"]
"""
        (base_dir / "Dockerfile").write_text(dockerfile_content)

    def _setup_pip_install(self, base_dir: Path, version: str) -> None:
        """Set up PyPI-based installation."""
        # Create empty repo dir for compatibility
        repo_dir = paths.repos_dir() / "vldmcp"
        repo_dir.mkdir(parents=True, exist_ok=True)

        version_spec = version if version != "unknown" else ""

        # Create Dockerfile
        dockerfile_content = f"""FROM python:3.10-slim

WORKDIR /app

# Install from PyPI
RUN pip install vldmcp{f'=={version_spec}' if version_spec else ''}

# Version: {version}
CMD ["vldmcp"]
"""
        (base_dir / "Dockerfile").write_text(dockerfile_content)

    def uninstall(self, purge: bool = False) -> List[Tuple[str, Path]]:
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
            # Run natively
            server_id = self.backend.start({}, [])
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
