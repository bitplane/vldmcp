"""Tests for the daemon service."""

import os
import time
import tempfile
from pathlib import Path

import pytest

from vldmcp.service.system.daemon import DaemonService


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_daemon_init(temp_dir):
    """Test daemon service initialization."""
    pid_file = temp_dir / "test.pid"
    daemon = DaemonService(["echo", "test"], pid_file)
    assert daemon._command == ["echo", "test"]
    assert daemon._pid_file == pid_file
    assert daemon._process is None
    assert daemon._pid is None


def test_daemon_init_loads_existing_pid(temp_dir):
    """Test that daemon loads existing PID on init."""
    pid_file = temp_dir / "test.pid"
    # Use current PID so it's valid
    test_pid = str(os.getpid())
    pid_file.write_text(test_pid)

    daemon = DaemonService(["echo", "test"], pid_file)
    assert daemon._pid == test_pid


def test_daemon_init_removes_stale_pid(temp_dir):
    """Test that daemon removes stale PID file on init."""
    pid_file = temp_dir / "test.pid"
    # Non-existent PID
    pid_file.write_text("99999999")

    daemon = DaemonService(["echo", "test"], pid_file)
    assert daemon._pid is None
    assert not pid_file.exists()


def test_daemon_start_stop_echo(temp_dir):
    """Test starting and stopping echo process."""
    pid_file = temp_dir / "test.pid"
    log_dir = temp_dir / "logs"

    daemon = DaemonService(["echo", "test"], pid_file, log_dir)
    daemon.start()

    # Check PID file was created
    assert pid_file.exists()
    pid = pid_file.read_text().strip()
    assert pid.isdigit()

    # Wait for echo to complete
    time.sleep(0.5)

    # Check log file was created and has output
    log_file = log_dir / "vldmcp.log"
    assert log_file.exists()
    assert "test" in log_file.read_text()

    # Process should eventually be detected as stopped
    # (echo exits immediately but zombie might persist briefly)
    daemon.status()  # This will clean up the PID file if process is dead


def test_daemon_start_stop_sleep(temp_dir):
    """Test starting and stopping sleep process."""
    pid_file = temp_dir / "test.pid"
    log_dir = temp_dir / "logs"

    daemon = DaemonService(["sleep", "30"], pid_file, log_dir)
    daemon.start()

    # Check it's running
    assert daemon.status() == "running"
    assert daemon._pid is not None

    # Stop it
    daemon.stop()
    time.sleep(0.1)

    # Check it's stopped
    assert daemon.status() == "stopped"
    assert not pid_file.exists()


def test_daemon_already_running(temp_dir, capsys):
    """Test that starting doesn't create duplicate if already running."""
    pid_file = temp_dir / "test.pid"
    log_dir = temp_dir / "logs"

    daemon = DaemonService(["sleep", "30"], pid_file, log_dir)
    daemon.start()

    # Try to start again
    daemon.start()

    # Check output
    captured = capsys.readouterr()
    assert "already running" in captured.out.lower()

    # Clean up
    daemon.stop()


def test_daemon_status_methods(temp_dir):
    """Test status and _is_running methods."""
    pid_file = temp_dir / "test.pid"
    daemon = DaemonService(["echo", "test"], pid_file)

    # No PID
    assert daemon.status() == "stopped"
    assert not daemon._is_running()

    # Valid PID (use current process)
    daemon._pid = str(os.getpid())
    assert daemon.status() == "running"
    assert daemon._is_running()

    # Invalid PID
    daemon._pid = "99999999"
    assert not daemon._is_running()
    status = daemon.status()
    assert status == "stopped"
    assert daemon._pid is None  # Should be cleaned up


def test_daemon_get_pid(temp_dir):
    """Test get_pid method."""
    pid_file = temp_dir / "test.pid"
    daemon = DaemonService(["echo", "test"], pid_file)

    # No PID
    assert daemon.get_pid() is None

    # With PID
    daemon._pid = "12345"
    assert daemon.get_pid() == "12345"


def test_daemon_stop_dead_process(temp_dir):
    """Test stopping when process already dead."""
    pid_file = temp_dir / "test.pid"
    daemon = DaemonService(["echo", "test"], pid_file)
    daemon._pid = "99999999"  # Non-existent

    # Should not raise
    daemon.stop()
    assert daemon._pid is None


def test_multiple_daemons(temp_dir):
    """Test multiple daemon instances with different PID files."""
    pid_file1 = temp_dir / "daemon1.pid"
    pid_file2 = temp_dir / "daemon2.pid"
    log_dir = temp_dir / "logs"

    daemon1 = DaemonService(["sleep", "30"], pid_file1, log_dir)
    daemon2 = DaemonService(["sleep", "30"], pid_file2, log_dir)

    daemon1.start()
    daemon2.start()

    # Both should be running with different PIDs
    assert daemon1.status() == "running"
    assert daemon2.status() == "running"
    assert daemon1._pid != daemon2._pid
    assert pid_file1.exists()
    assert pid_file2.exists()

    # Stop both
    daemon1.stop()
    daemon2.stop()
