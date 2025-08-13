"""Native process runtime backend."""

import os
from pathlib import Path
from typing import List

from .base import RuntimeBackend


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
