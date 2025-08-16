"""Tests for native platform."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
import psutil

from vldmcp.service.platform.native import NativePlatform


def test_native_platform_creates_core_services(xdg_dirs):
    """Test that NativePlatform has all core services."""
    platform = NativePlatform()

    # Check that core services are registered
    assert platform.get_service("storage") is not None
    assert platform.get_service("keys") is not None
    assert platform.get_service("config") is not None
    assert platform.get_service("daemon") is not None


def test_native_deploy_creates_directories(xdg_dirs):
    """Test that NativePlatform.deploy() creates required directories."""
    platform = NativePlatform()

    # Run deploy
    result = platform.deploy()

    assert result is True
    assert platform.storage.data_dir().exists()
    assert platform.storage.config_dir().exists()
    assert platform.storage.state_dir().exists()
    assert platform.storage.cache_dir().exists()
    assert platform.storage.runtime_dir().exists()
    assert platform.storage.user_key_path().exists()


def test_native_deploy_preserves_existing_key(xdg_dirs):
    """Test that NativePlatform.deploy() preserves existing user key."""
    platform = NativePlatform()

    # Create a key file first
    key_path = platform.storage.user_key_path()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    test_key = b"test_key_content_32_bytes_exactly!" * 1  # 34 bytes, but we'll trim
    test_key = test_key[:32]  # Make it exactly 32 bytes
    key_path.write_bytes(test_key)

    # Run deploy
    result = platform.deploy()

    assert result is True
    assert key_path.exists()
    # Verify key wasn't changed
    assert key_path.read_bytes() == test_key


def test_native_deploy_idempotent(xdg_dirs):
    """Test that NativePlatform.deploy() can be run multiple times."""
    platform = NativePlatform()

    # First deploy
    result1 = platform.deploy()
    assert result1 is True

    # Get the key that was created
    key_path = platform.storage.user_key_path()
    original_key = key_path.read_bytes()

    # Second deploy - should succeed and not change the key
    result2 = platform.deploy()
    assert result2 is True
    assert key_path.read_bytes() == original_key


def test_native_deploy_creates_key(xdg_dirs):
    """Test that NativePlatform.deploy() creates user key."""
    platform = NativePlatform()

    # deploy should create directories and user key
    result = platform.deploy()

    assert result is True
    assert platform.storage.user_key_path().exists()


def test_native_build_if_needed_returns_true(xdg_dirs):
    """Test that NativePlatform.build_if_needed() returns True (no build needed)."""
    platform = NativePlatform()

    # Native platform doesn't need building
    result = platform.build_if_needed()

    assert result is True


def test_native_platform_service_lifecycle(xdg_dirs):
    """Test that NativePlatform can start and stop services."""
    platform = NativePlatform()

    # Start a service
    platform.start_service("storage")
    storage_service = platform.get_service("storage")
    assert storage_service.status() == "running"

    # Stop a service
    platform.stop_service("storage")
    assert storage_service.status() == "stopped"


def test_native_platform_status_aggregation(xdg_dirs):
    """Test that NativePlatform aggregates service statuses."""
    platform = NativePlatform()

    # Start some services
    platform.start_service("storage")
    platform.start_service("keys")

    # Get overall status
    statuses = platform.get_all_statuses()

    assert "storage" in statuses
    assert "keys" in statuses
    assert statuses["storage"] == "running"
    assert statuses["keys"] == "running"


def test_start_calls_super():
    """Test that start() calls super().start()."""
    platform = NativePlatform()
    platform.storage = MagicMock()

    # Mock the storage service to avoid file operations
    pid_file = MagicMock()
    pid_file.exists.return_value = False
    platform.storage.pid_file_path.return_value = pid_file

    with (
        patch.object(platform.__class__.__bases__[0], "start") as mock_super_start,
        patch("subprocess.Popen") as mock_popen,
        patch("psutil.Process"),
    ):
        mock_popen.return_value.pid = 12345
        platform.start()

        mock_super_start.assert_called_once()


def test_native_platform_upgrade():
    """Test native platform upgrade."""
    platform = NativePlatform()

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        result = platform.upgrade()

        assert result is True
        mock_run.assert_called_once()


def test_native_platform_logs():
    """Test native platform logs."""
    platform = NativePlatform()

    logs = platform.logs()

    assert isinstance(logs, str)
    assert "Native platform logs not yet implemented" in logs


def test_start_with_existing_daemon():
    """Test starting platform when daemon is already running."""
    platform = NativePlatform()

    existing_pid = 12345

    # Mock the storage service and PID file
    mock_storage = MagicMock()
    mock_pid_file = MagicMock()
    mock_storage.pid_file_path.return_value = mock_pid_file
    platform.storage = mock_storage

    # Mock existing PID file and running process
    mock_pid_file.exists.return_value = True
    mock_pid_file.read_text.return_value = str(existing_pid)

    with (
        patch("psutil.pid_exists", return_value=True),
        patch("psutil.Process") as mock_process,
        patch.object(platform.__class__.__bases__[0], "start"),
    ):  # Skip service startup
        platform.start()

        # Should attach to existing process, not start new one
        mock_process.assert_called_once_with(existing_pid)
        assert platform._daemon_process == mock_process.return_value


def test_start_with_stale_pid_file():
    """Test starting platform with stale PID file."""
    platform = NativePlatform()

    stale_pid = 99999

    # Mock the storage service and PID file
    mock_storage = MagicMock()
    mock_pid_file = MagicMock()
    mock_storage.pid_file_path.return_value = mock_pid_file
    platform.storage = mock_storage

    mock_pid_file.exists.return_value = True
    mock_pid_file.read_text.return_value = str(stale_pid)

    # Need to trigger the exception handling path for cleanup
    with (
        patch("psutil.pid_exists", side_effect=psutil.NoSuchProcess(stale_pid)),
        patch("subprocess.Popen") as mock_popen,
        patch("psutil.Process") as mock_process,
        patch.object(platform.__class__.__bases__[0], "start"),
    ):
        mock_popen.return_value.pid = 54321

        platform.start()

        # Should clean up stale PID file
        mock_pid_file.unlink.assert_called_once_with(missing_ok=True)
        # Should start new daemon process
        mock_popen.assert_called_once()
        mock_process.assert_called_with(54321)


def test_start_new_daemon():
    """Test starting platform with no existing daemon."""
    platform = NativePlatform()

    new_pid = 11111

    # Mock the storage service and PID file
    mock_storage = MagicMock()
    mock_pid_file = MagicMock()
    mock_storage.pid_file_path.return_value = mock_pid_file
    platform.storage = mock_storage

    mock_pid_file.exists.return_value = False

    with (
        patch("subprocess.Popen") as mock_popen,
        patch("psutil.Process") as mock_process,
        patch.object(platform.__class__.__bases__[0], "start"),
    ):
        mock_popen.return_value.pid = new_pid

        platform.start()

        # Should start new daemon
        mock_popen.assert_called_once_with(
            ["vldmcpd"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        mock_process.assert_called_with(new_pid)
        mock_pid_file.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_pid_file.write_text.assert_called_once_with(str(new_pid))


def test_start_with_invalid_pid_file():
    """Test starting platform with invalid PID file content."""
    platform = NativePlatform()

    # Mock the storage service and PID file
    mock_storage = MagicMock()
    mock_pid_file = MagicMock()
    mock_storage.pid_file_path.return_value = mock_pid_file
    platform.storage = mock_storage

    mock_pid_file.exists.return_value = True
    mock_pid_file.read_text.return_value = "not-a-number"

    with (
        patch("subprocess.Popen") as mock_popen,
        patch("psutil.Process"),
        patch.object(platform.__class__.__bases__[0], "start"),
    ):
        mock_popen.return_value.pid = 11111

        platform.start()

        # Should clean up invalid PID file and start new daemon
        mock_pid_file.unlink.assert_called_once_with(missing_ok=True)
        mock_popen.assert_called_once()


def test_start_with_no_such_process_error():
    """Test starting platform when process lookup raises NoSuchProcess."""
    platform = NativePlatform()

    stale_pid = 99999

    # Mock the storage service and PID file
    mock_storage = MagicMock()
    mock_pid_file = MagicMock()
    mock_storage.pid_file_path.return_value = mock_pid_file
    platform.storage = mock_storage

    mock_pid_file.exists.return_value = True
    mock_pid_file.read_text.return_value = str(stale_pid)

    with (
        patch("psutil.pid_exists", side_effect=psutil.NoSuchProcess(stale_pid)),
        patch("subprocess.Popen") as mock_popen,
        patch("psutil.Process"),
        patch.object(platform.__class__.__bases__[0], "start"),
    ):
        mock_popen.return_value.pid = 54321

        platform.start()

        # Should handle NoSuchProcess and clean up PID file
        mock_pid_file.unlink.assert_called_once_with(missing_ok=True)
        mock_popen.assert_called_once()


def test_stop_running_daemon():
    """Test stopping a running daemon."""
    platform = NativePlatform()

    # Mock the storage service and PID file
    mock_storage = MagicMock()
    mock_pid_file = MagicMock()
    mock_storage.pid_file_path.return_value = mock_pid_file
    platform.storage = mock_storage

    mock_daemon = MagicMock()
    mock_daemon.is_running.return_value = True
    platform._daemon_process = mock_daemon

    # Mock successful graceful shutdown
    mock_daemon.is_running.side_effect = [True, False]  # running, then stopped

    platform.stop()

    mock_daemon.terminate.assert_called_once()
    mock_daemon.wait.assert_called_once_with(timeout=10)
    mock_pid_file.unlink.assert_called_once_with(missing_ok=True)


def test_stop_daemon_timeout_force_kill():
    """Test stopping daemon that doesn't respond to graceful shutdown."""
    platform = NativePlatform()

    # Mock the storage service and PID file
    mock_storage = MagicMock()
    mock_pid_file = MagicMock()
    mock_storage.pid_file_path.return_value = mock_pid_file
    platform.storage = mock_storage

    mock_daemon = MagicMock()
    mock_daemon.is_running.return_value = True
    platform._daemon_process = mock_daemon

    # Mock timeout on graceful shutdown
    mock_daemon.wait.side_effect = [psutil.TimeoutExpired(10), None]
    mock_daemon.is_running.side_effect = [True, False]  # running, then stopped

    platform.stop()

    mock_daemon.terminate.assert_called_once()
    mock_daemon.kill.assert_called_once()
    assert mock_daemon.wait.call_count == 2
    mock_pid_file.unlink.assert_called_once_with(missing_ok=True)


def test_stop_daemon_no_such_process():
    """Test stopping daemon when process is already gone."""
    platform = NativePlatform()

    # Mock the storage service and PID file
    mock_storage = MagicMock()
    mock_pid_file = MagicMock()
    mock_storage.pid_file_path.return_value = mock_pid_file
    platform.storage = mock_storage

    mock_daemon = MagicMock()
    mock_daemon.is_running.return_value = True
    mock_daemon.terminate.side_effect = psutil.NoSuchProcess(12345)
    platform._daemon_process = mock_daemon

    with patch.object(platform.__class__.__bases__[0], "stop"):
        platform.stop()

    mock_daemon.terminate.assert_called_once()
    # Should handle NoSuchProcess gracefully - process already gone so no cleanup of PID file
    mock_pid_file.unlink.assert_not_called()


def test_stop_no_daemon():
    """Test stopping when no daemon is running."""
    platform = NativePlatform()

    # Mock the storage service and PID file
    mock_storage = MagicMock()
    mock_pid_file = MagicMock()
    mock_storage.pid_file_path.return_value = mock_pid_file
    platform.storage = mock_storage

    platform._daemon_process = None

    platform.stop()

    # Should just clean up PID file
    mock_pid_file.unlink.assert_called_once_with(missing_ok=True)


def test_upgrade_success():
    """Test successful upgrade."""
    platform = NativePlatform()

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = platform.upgrade()

        assert result is True
        mock_run.assert_called_once_with(
            ["pip", "install", "--upgrade", "vldmcp"], capture_output=True, text=True, check=True
        )


def test_upgrade_failure():
    """Test failed upgrade."""
    platform = NativePlatform()

    with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "pip")):
        result = platform.upgrade()

        assert result is False


def test_build_always_returns_true():
    """Test that build method always returns True for native platform."""
    platform = NativePlatform()
    dockerfile_path = Path("/fake/dockerfile")

    result = platform.build(dockerfile_path)

    assert result is True
