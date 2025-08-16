"""Unit tests for NativePlatform functionality."""

from vldmcp.platform import NativePlatform


def test_native_platform_creates_core_services(xdg_dirs):
    """Test that NativePlatform has all core services."""
    platform = NativePlatform()

    # Check that core services are registered
    assert platform.get_service("files") is not None
    assert platform.get_service("keys") is not None
    assert platform.get_service("config") is not None
    assert platform.get_service("installer") is not None
    assert platform.get_service("daemon") is not None


def test_native_install_creates_directories(xdg_dirs):
    """Test that NativePlatform.install() creates required directories."""
    platform = NativePlatform()

    # Run install
    result = platform.install()

    assert result is True
    assert platform.files.data_dir().exists()
    assert platform.files.config_dir().exists()
    assert platform.files.state_dir().exists()
    assert platform.files.cache_dir().exists()
    assert platform.files.runtime_dir().exists()
    assert platform.files.user_key_path().exists()


def test_native_install_preserves_existing_key(xdg_dirs):
    """Test that NativePlatform.install() preserves existing user key."""
    platform = NativePlatform()

    # Create a key file first
    key_path = platform.files.user_key_path()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    test_key = b"test_key_content_32_bytes_exactly!" * 1  # 34 bytes, but we'll trim
    test_key = test_key[:32]  # Make it exactly 32 bytes
    key_path.write_bytes(test_key)

    # Run install
    result = platform.install()

    assert result is True
    assert key_path.exists()
    # Verify key wasn't changed
    assert key_path.read_bytes() == test_key


def test_native_install_idempotent(xdg_dirs):
    """Test that NativePlatform.install() can be run multiple times."""
    platform = NativePlatform()

    # First install
    result1 = platform.install()
    assert result1 is True

    # Get the key that was created
    key_path = platform.files.user_key_path()
    original_key = key_path.read_bytes()

    # Second install - should succeed and not change the key
    result2 = platform.install()
    assert result2 is True
    assert key_path.read_bytes() == original_key


def test_native_deploy_calls_install(xdg_dirs):
    """Test that NativePlatform.deploy() calls install."""
    platform = NativePlatform()

    # deploy should call install() and build_if_needed()
    result = platform.deploy()

    assert result is True
    assert platform.files.user_key_path().exists()


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
    platform.start_service("files")
    files_service = platform.get_service("files")
    assert files_service.status() == "running"

    # Stop a service
    platform.stop_service("files")
    assert files_service.status() == "stopped"


def test_native_platform_status_aggregation(xdg_dirs):
    """Test that NativePlatform aggregates service statuses."""
    platform = NativePlatform()

    # Start some services
    platform.start_service("files")
    platform.start_service("keys")

    # Get overall status
    statuses = platform.get_all_statuses()

    assert "files" in statuses
    assert "keys" in statuses
    assert statuses["files"] == "running"
    assert statuses["keys"] == "running"
