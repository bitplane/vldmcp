"""Abstract base class for runtime backends."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


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

    def stream_logs(self, server_id: str) -> None:
        """Stream server logs to stdout (default implementation prints static logs)."""
        logs = self.logs(server_id)
        print(logs)
