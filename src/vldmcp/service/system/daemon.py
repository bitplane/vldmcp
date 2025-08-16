"""Daemon service for vldmcp."""

import subprocess
import signal
import os
from .. import Service


class DaemonService(Service):
    """Service that manages the vldmcp daemon process."""

    def __init__(self):
        super().__init__()
        self._process = None
        self._pid = None

    @classmethod
    def name(cls) -> str:
        return "daemon"

    def start(self, debug: bool = False):
        """Start the daemon process.

        Args:
            debug: If True, run in foreground for debugging
        """
        if self._running:
            return

        pid_file = self.parent.storage.pid_file_path()

        if debug:
            # Run in foreground for debugging
            self._process = subprocess.Popen(["vldmcpd"])
            self._pid = str(self._process.pid)
        else:
            # Run as daemon
            self._process = subprocess.Popen(
                ["vldmcpd", "--daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            # Read PID from file
            if pid_file.exists():
                self._pid = pid_file.read_text().strip()

        self._running = True

    def stop(self):
        """Stop the daemon process."""
        if not self._running:
            return

        if self._process:
            # Direct process reference
            self._process.terminate()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
        elif self._pid:
            # PID-based termination
            try:
                os.kill(int(self._pid), signal.SIGTERM)
            except (ProcessLookupError, ValueError):
                pass  # Process already dead or invalid PID

        self._process = None
        self._pid = None
        self._running = False

    def status(self) -> str:
        """Get daemon status."""
        if self._process:
            if self._process.poll() is None:
                return "running"
            else:
                return "stopped"
        elif self._pid:
            try:
                # Check if PID is still running
                os.kill(int(self._pid), 0)
                return "running"
            except (ProcessLookupError, ValueError):
                return "stopped"
        return "stopped"

    def get_pid(self) -> str | None:
        """Get the daemon PID.

        Returns:
            PID as string, or None if not running
        """
        if self._pid:
            return self._pid
        if self._process:
            return str(self._process.pid)
        return None

    def logs(self) -> str:
        """Get daemon logs.

        Returns:
            Log content as string
        """
        # TODO: Implement log retrieval
        # For now, return placeholder
        return "Daemon logs not yet implemented"

    def stream_logs(self) -> None:
        """Stream daemon logs to stdout."""
        # TODO: Implement log streaming
        print(self.logs())
