"""Daemon service for vldmcp."""

import subprocess
import signal
import os
from pathlib import Path
from ..base import Service
from ...util.paths import Paths


class DaemonService(Service):
    """Service that manages a daemon process."""

    def __init__(self, command: list[str], pid_file: Path, log_dir: Path = None, parent=None):
        super().__init__(parent)
        self._command = command
        self._pid_file = pid_file
        self._log_dir = log_dir
        self._process = None
        self._pid = None

        # Load existing PID if daemon is already running
        self._load_pid()

    def _load_pid(self):
        """Load PID from file if daemon is already running."""
        if self._pid_file.exists():
            try:
                pid = int(self._pid_file.read_text().strip())
                # Check if process is actually running
                os.kill(pid, 0)
                self._pid = str(pid)
            except (ValueError, ProcessLookupError, OSError):
                # PID file is stale, remove it
                self._pid_file.unlink(missing_ok=True)
                self._pid = None

    def start(self):
        """Start the daemon process."""
        self._pid_file.parent.mkdir(parents=True, exist_ok=True)

        # Check if already running
        if self._pid and self._is_running():
            print(f"Daemon already running with PID {self._pid}")
            return

        # Set up log files
        if self._log_dir:
            log_dir = self._log_dir
        else:
            log_dir = Paths.STATE / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        stdout_log = log_dir / "vldmcp.log"
        stderr_log = log_dir / "vldmcp.err"

        # Start daemon in background, detached from terminal
        with open(stdout_log, "a") as out, open(stderr_log, "a") as err:
            self._process = subprocess.Popen(
                self._command,
                stdout=out,
                stderr=err,
                stdin=subprocess.DEVNULL,
                start_new_session=True,  # Create new session (detach from terminal)
            )
            self._pid = str(self._process.pid)

        # Write PID file
        self._pid_file.write_text(self._pid)

        # Mark as running
        super().start()

    def stop(self):
        """Stop the daemon process."""
        if self._pid:
            try:
                pid = int(self._pid)
                # Send SIGTERM for graceful shutdown
                os.kill(pid, signal.SIGTERM)
                # TODO: Add timeout and SIGKILL if needed
            except (ProcessLookupError, ValueError):
                pass  # Process already dead

            # Clean up PID file
            self._pid_file.unlink(missing_ok=True)

        self._process = None
        self._pid = None
        super().stop()

    def status(self) -> str:
        """Get daemon status."""
        if not self._pid:
            return "stopped"

        if self._is_running():
            return "running"
        else:
            # Process died but PID file exists - clean it up
            self._pid_file.unlink(missing_ok=True)
            self._pid = None
            return "stopped"

    def _is_running(self) -> bool:
        """Check if the daemon process is running."""
        if not self._pid:
            return False

        try:
            # Signal 0 doesn't kill, just checks if process exists
            os.kill(int(self._pid), 0)
            return True
        except (ProcessLookupError, ValueError):
            return False

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
