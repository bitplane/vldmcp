"""Daemon service for vldmcp."""

import subprocess
import signal
import os
from ..base import Service


class DaemonService(Service):
    """Service that manages a daemon process."""

    def __init__(self, command: list[str], parent=None):
        super().__init__(parent)
        self._command = command
        self._process = None
        self._pid = None

    def start(self):
        """Start the daemon process."""
        super().start()

        pid_file = self.parent.storage.pid_file_path()
        pid_file.parent.mkdir(parents=True, exist_ok=True)

        # Run the command
        self._process = subprocess.Popen(self._command)
        self._pid = str(self._process.pid)

        # Write PID file
        pid_file.write_text(str(self._process.pid))

    def stop(self):
        """Stop the daemon process."""
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

        super().stop()

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
