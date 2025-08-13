"""Native process runtime backend."""

import os
import subprocess
from pathlib import Path
from typing import Optional

from .. import paths
from .base import RuntimeBackend


class NativeBackend(RuntimeBackend):
    """Native process runtime backend (no container)."""

    def build(self, dockerfile_path: Path) -> bool:
        """No build needed for native."""
        return True

    def start(self, mounts: dict[str, str], ports: list[str]) -> str:
        """Start native server process."""
        # Start the daemon in the background
        proc = subprocess.Popen(
            ["vldmcpd"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return str(proc.pid)

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

    def deploy_start(self, debug: bool = False) -> Optional[str]:
        """Deploy and start native server."""
        # Auto-deploy if needed
        if not self.deploy():
            return None

        # Check if already running
        pid_file = paths.pid_file_path()
        if pid_file.exists():
            try:
                pid_content = pid_file.read_text().strip()
                # Check if still running
                os.kill(int(pid_content), 0)
                return None  # Already running
            except (OSError, ValueError):
                # Stale PID file, remove it
                pid_file.unlink()

        # Start the server
        server_id = self.start({}, [])

        # Write PID file
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(server_id)

        return server_id

    def deploy_stop(self) -> bool:
        """Stop native server."""
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
        """Get native server status."""
        pid_file = paths.pid_file_path()

        if not pid_file.exists():
            return "not running"

        pid_content = pid_file.read_text().strip()
        status = self.status(pid_content)

        # Clean up stale PID file
        if status in ["stopped", "not found"]:
            pid_file.unlink()

        return status
