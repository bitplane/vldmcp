"""Process management utilities."""

import os
import signal
import time
from pathlib import Path


def kill_process_gracefully(pid: int, timeout: int = 10) -> bool:
    """Kill a process gracefully with SIGTERM, then SIGKILL if needed.

    Args:
        pid: Process ID to kill
        timeout: Time to wait for graceful shutdown before force kill

    Returns:
        True if process was killed, False if process didn't exist
    """
    try:
        # Check if process exists
        os.kill(pid, 0)
    except (OSError, ProcessLookupError):
        # Process doesn't exist
        return False

    try:
        # Try graceful shutdown with SIGTERM
        os.kill(pid, signal.SIGTERM)

        # Wait for process to exit
        for _ in range(timeout * 10):  # Check every 100ms
            try:
                os.kill(pid, 0)
                time.sleep(0.1)
            except (OSError, ProcessLookupError):
                # Process has exited
                return True

        # Process still alive, force kill
        os.kill(pid, signal.SIGKILL)
        return True

    except (OSError, ProcessLookupError):
        # Process exited during our attempts
        return True


def kill_process_from_pidfile(pidfile_path: Path, timeout: int = 10) -> bool:
    """Kill process using PID from file, then remove the PID file.

    Args:
        pidfile_path: Path to PID file
        timeout: Time to wait for graceful shutdown

    Returns:
        True if process was killed or didn't exist, False on error
    """
    if not pidfile_path.exists():
        return True  # No PID file means no process running

    try:
        pid_content = pidfile_path.read_text().strip()

        # Handle container PIDs (format: "container:123")
        if pid_content.startswith("container:"):
            # For container PIDs, we don't kill directly - the runtime handles it
            return True

        pid = int(pid_content)
        result = kill_process_gracefully(pid, timeout)

        # Remove PID file if kill was successful
        if result:
            pidfile_path.unlink()

        return result

    except (ValueError, OSError):
        # Invalid PID file or other error
        # Remove the stale PID file
        try:
            pidfile_path.unlink()
        except OSError:
            pass
        return False


def is_process_running(pid: int) -> bool:
    """Check if a process is running.

    Args:
        pid: Process ID to check

    Returns:
        True if process exists, False otherwise
    """
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False
