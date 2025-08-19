"""Native process platform backend."""

from .base import Platform
from ..system.daemon import DaemonService
from ...util.paths import Paths


class NativePlatform(Platform):
    """Native process platform backend (no container)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.daemon = DaemonService(["vldmcpd"], self.storage.pid_file_path(), None, self)

    def build(self, force: bool = False) -> bool:
        """No build needed for native."""
        return True

    def status(self) -> str:
        """Get platform status by checking daemon."""
        if not Paths.CONFIG.exists():
            return "not deployed"

        return self.daemon.status()
