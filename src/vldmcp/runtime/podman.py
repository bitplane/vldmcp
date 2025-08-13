"""Podman container runtime backend."""

import json
import subprocess
from pathlib import Path

from ..models.disk_usage import DiskUsage
from .base import RuntimeBackend


class PodmanBackend(RuntimeBackend):
    """Podman container runtime backend."""

    def build(self, dockerfile_path: Path) -> bool:
        """Build container with podman."""
        result = subprocess.run(
            ["podman", "build", "-t", "vldmcp:latest", str(dockerfile_path.parent)], capture_output=True
        )
        return result.returncode == 0

    def start(self, mounts: dict[str, str], ports: list[str]) -> str:
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

    def stream_logs(self, server_id: str) -> None:
        """Stream podman container logs to stdout."""
        subprocess.run(["podman", "logs", "-f", "vldmcp-server"], check=True)

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
