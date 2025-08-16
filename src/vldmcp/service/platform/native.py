"""Native process platform backend."""

import subprocess
from pathlib import Path

import psutil

from .base import PlatformBackend


class NativePlatform(PlatformBackend):
    """Native process platform backend (no container)."""

    def __init__(self):
        super().__init__()
        self._daemon_process = None

    def build(self, dockerfile_path: Path) -> bool:
        """No build needed for native."""
        return True

    def start(self):
        """Start the native platform (which starts vldmcpd daemon)."""
        # Start child services first
        super().start()

        # Check for existing daemon
        pid_file = self.storage.pid_file_path()
        if pid_file.exists():
            try:
                existing_pid = int(pid_file.read_text().strip())
                if psutil.pid_exists(existing_pid):
                    # Daemon already running
                    self._daemon_process = psutil.Process(existing_pid)
                    return
            except (ValueError, psutil.NoSuchProcess):
                # Stale PID file, clean it up
                pid_file.unlink(missing_ok=True)

        # Start the vldmcpd daemon
        proc = subprocess.Popen(
            ["vldmcpd"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self._daemon_process = psutil.Process(proc.pid)

        # Write PID file
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(proc.pid))

    def stop(self):
        """Stop the native platform (which stops vldmcpd daemon)."""
        daemon_process = getattr(self, "_daemon_process", None)
        pid_file = self.storage.pid_file_path()

        if daemon_process and daemon_process.is_running():
            try:
                # Try graceful shutdown first
                daemon_process.terminate()
                daemon_process.wait(timeout=10)
            except psutil.TimeoutExpired:
                # Force kill if graceful shutdown failed
                daemon_process.kill()
                daemon_process.wait(timeout=5)
            except psutil.NoSuchProcess:
                # Process already gone
                pass

            # Only remove PID file if process actually stopped
            if not daemon_process.is_running():
                pid_file.unlink(missing_ok=True)
        else:
            # No running process, just clean up PID file
            pid_file.unlink(missing_ok=True)

        # Stop child services
        super().stop()

    def upgrade(self) -> bool:
        """Upgrade vldmcp using pip."""
        try:
            result = subprocess.run(
                ["pip", "install", "--upgrade", "vldmcp"], capture_output=True, text=True, check=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False

    def logs(self) -> str:
        """Get platform logs."""
        # TODO: Implement actual log retrieval
        return "Native platform logs not yet implemented"
