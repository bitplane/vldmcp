"""Podman container runtime backend."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from .. import __version__, paths
from ..config import get_config
from ..models.disk_usage import DiskUsage
from .base import RuntimeBackend


class PodmanBackend(RuntimeBackend):
    """Podman container runtime backend."""

    def _get_podman_config(self):
        """Get podman-specific configuration values."""
        config = get_config()
        if hasattr(config.runtime, "image_name") and hasattr(config.runtime, "container_name"):
            return config.runtime.image_name, config.runtime.container_name
        # Fallback to defaults if config doesn't have podman-specific fields
        return "vldmcp:latest", "vldmcp-server"

    def build(self, dockerfile_path: Path) -> bool:
        """Build container with podman."""
        # Get config values
        image_name, _ = self._get_podman_config()

        # Build with version spec if we have a known version
        version_spec = f"=={__version__}" if __version__ != "unknown" else ""

        result = subprocess.run(
            [
                "podman",
                "build",
                "--build-arg",
                f"VERSION_SPEC={version_spec}",
                "-t",
                image_name,
                str(dockerfile_path.parent),
            ],
            capture_output=True,
        )
        return result.returncode == 0

    def start(self, mounts: dict[str, str], ports: list[str]) -> str:
        """Start container with podman."""
        # Get config values
        image_name, container_name = self._get_podman_config()

        cmd = ["podman", "run", "-d", "--name", container_name]

        # Add mounts
        for host_path, container_path in mounts.items():
            mode = "ro" if container_path.endswith(":ro") else "rw"
            container_path = container_path.replace(":ro", "").replace(":rw", "")
            cmd.extend(["-v", f"{host_path}:{container_path}:{mode}"])

        # Add ports
        for port in ports:
            cmd.extend(["-p", port])

        cmd.append(image_name)

        subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Get container PID
        pid_result = subprocess.run(
            ["podman", "inspect", "--format", "{{.State.Pid}}", container_name],
            capture_output=True,
            text=True,
            check=True,
        )
        return f"container:{pid_result.stdout.strip()}"

    def stop(self, server_id: str) -> bool:
        """Stop podman container."""
        _, container_name = self._get_podman_config()
        subprocess.run(["podman", "stop", container_name], check=True)
        subprocess.run(["podman", "rm", container_name], check=True)
        return True

    def status(self, server_id: str) -> str:
        """Check podman container status."""
        _, container_name = self._get_podman_config()
        result = subprocess.run(
            ["podman", "ps", "-a", "--filter", f"name={container_name}"], capture_output=True, text=True
        )
        if container_name in result.stdout:
            if "Up" in result.stdout:
                return "running"
            else:
                return "stopped"
        return "not found"

    def logs(self, server_id: str) -> str:
        """Get podman container logs."""
        _, container_name = self._get_podman_config()
        result = subprocess.run(["podman", "logs", container_name], capture_output=True, text=True)
        return result.stdout

    def stream_logs(self, server_id: str) -> None:
        """Stream podman container logs to stdout."""
        _, container_name = self._get_podman_config()
        subprocess.run(["podman", "logs", "-f", container_name], check=True)

    def du(self) -> DiskUsage:
        """Get disk usage including container images and volumes.

        Returns:
            DiskUsage model with sizes in bytes by functional area including container storage
        """
        # Get base sizes from parent implementation
        usage = super().du()

        # Get container image sizes
        images_size = 0
        try:
            # Get all vldmcp-related images
            result = subprocess.run(
                ["podman", "images", "--format", "json", "--filter", "reference=vldmcp*"],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                images = json.loads(result.stdout)
                for image in images:
                    if "Size" in image:
                        images_size += image["Size"]
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            pass

        # Get container volumes size - add to mcp.data
        volumes_size = 0
        try:
            # Get volumes used by vldmcp containers
            result = subprocess.run(
                ["podman", "volume", "ls", "--format", "json"], capture_output=True, text=True, check=True
            )
            if result.stdout:
                volumes = json.loads(result.stdout)
                for volume in volumes:
                    if "Name" in volume and "vldmcp" in volume["Name"]:
                        # Get size of this volume
                        vol_result = subprocess.run(
                            ["podman", "volume", "inspect", volume["Name"]], capture_output=True, text=True, check=True
                        )
                        if vol_result.stdout:
                            vol_info = json.loads(vol_result.stdout)
                            if vol_info and "Mountpoint" in vol_info[0]:
                                mount = vol_info[0]["Mountpoint"]
                                # Get size of mountpoint
                                du_result = subprocess.run(
                                    ["du", "-sb", mount], capture_output=True, text=True, check=True
                                )
                                volumes_size += int(du_result.stdout.split()[0])
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, ValueError):
            pass

        # Update container-specific sizes
        usage.mcp.images = images_size
        usage.mcp.data += volumes_size

        return usage

    def build_if_needed(self) -> bool:
        """Build container image if needed."""
        base_dir = paths.install_dir() / "base"
        if not base_dir.exists():
            return False

        dockerfile = base_dir / "Dockerfile"
        if not dockerfile.exists():
            return False

        return self.build(dockerfile)

    def install(self) -> bool:
        """Install container environment (creates Dockerfile)."""
        # Call parent install for basic setup
        if not super().install():
            return False

        # Set up install directory for container assets
        install_dir = paths.install_dir()
        base_dir = install_dir / "base"
        base_dir.mkdir(parents=True, exist_ok=True)

        # Create Dockerfile for PyPI installation
        self._create_dockerfile(base_dir)

        return True

    def _create_dockerfile(self, base_dir: Path) -> None:
        """Copy Dockerfile template to build directory."""
        # Get the template Dockerfile from the runtime package
        template_path = Path(__file__).parent / "assets" / "Dockerfile"
        target_path = base_dir / "Dockerfile"

        # Copy the template (version is handled via build args)
        shutil.copy2(template_path, target_path)

    def upgrade(self) -> bool:
        """Upgrade vldmcp (pip upgrade + rebuild container)."""
        try:
            # First upgrade the host package
            result = subprocess.run(
                ["pip", "install", "--upgrade", "vldmcp"], capture_output=True, text=True, check=True
            )
            if result.returncode != 0:
                return False

            # Then rebuild the container with new version
            return self.build_if_needed()
        except subprocess.CalledProcessError:
            return False

    def deploy_start(self, debug: bool = False) -> Optional[str]:
        """Deploy and start container server."""
        # Auto-deploy if needed
        if not self.deploy():
            return None

        # Check if already running
        pid_file = paths.pid_file_path()
        if pid_file.exists():
            try:
                pid_content = pid_file.read_text().strip()
                # Check if still running
                if pid_content.startswith("container:"):
                    status = self.status(pid_content)
                    if status == "running":
                        return None  # Already running
            except (OSError, ValueError):
                pass
            # Remove stale PID file
            pid_file.unlink()

        # Get config for ports and other settings
        config = get_config()

        # Create mount mappings
        mounts = {
            str(paths.state_dir()): "/var/lib/vldmcp:rw",
            str(paths.cache_dir()): "/var/cache/vldmcp:rw",
            str(paths.config_dir()): "/etc/vldmcp:ro",
            str(paths.runtime_dir()): "/run/vldmcp:rw",
            str(paths.www_dir()): "/var/lib/vldmcp/www:rw",
        }

        # Get ports from config
        ports = []
        if hasattr(config.runtime, "ports"):
            ports = config.runtime.ports

        # Start container
        server_id = self.start(mounts, ports)

        # Write PID file
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(server_id)

        return server_id

    def deploy_stop(self) -> bool:
        """Stop container server."""
        pid_file = paths.pid_file_path()

        if not pid_file.exists():
            return False

        pid_content = pid_file.read_text().strip()
        result = self.stop(pid_content)

        # Remove PID file
        if result:
            pid_file.unlink()

        return result

    def deploy_status(self) -> str:
        """Get container server status."""
        pid_file = paths.pid_file_path()

        if not pid_file.exists():
            return "not running"

        pid_content = pid_file.read_text().strip()
        status = self.status(pid_content)

        # Clean up stale PID file
        if status in ["stopped", "not found"]:
            pid_file.unlink()

        return status
