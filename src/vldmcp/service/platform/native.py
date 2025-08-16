"""Native process platform backend."""

from .base import Platform
from ..system.daemon import DaemonService


class NativePlatform(Platform):
    """Native process platform backend (no container)."""

    def __init__(self):
        super().__init__()
        self.add_service(DaemonService())

    def build(self, force: bool = False) -> bool:
        """No build needed for native."""
        return True

    def status(self) -> str:
        """Get platform status by checking daemon."""
        if not self.storage.config_dir().exists():
            return "not deployed"

        daemon = self.get_service("daemon")
        return daemon.status() if daemon else "stopped"
