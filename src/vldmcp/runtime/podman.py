"""Podman container runtime backend."""

import subprocess
from pathlib import Path
from typing import List

from .base import RuntimeBackend


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

    def stream_logs(self, server_id: str) -> None:
        """Stream podman container logs to stdout."""
        subprocess.run(["podman", "logs", "-f", "vldmcp-server"], check=True)
