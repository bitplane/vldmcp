"""Tests for native platform."""

from vldmcp.service.platform.native import NativePlatform


def test_native_platform_creates_core_services(xdg_dirs):
    """Test that NativePlatform has all core services."""
    platform = NativePlatform()

    # Check that core services are registered
    assert platform.get_service("storage") is not None
    assert platform.get_service("config") is not None
    assert platform.get_service("crypto") is not None
    assert platform.get_service("daemon") is not None


def test_native_deploy_creates_directories(xdg_dirs):
    """Test that NativePlatform.deploy() creates required directories."""
    platform = NativePlatform()

    # Run deploy
    result = platform.deploy()

    assert result is True
    assert platform.storage.data_dir().exists()
    assert platform.storage.config_dir().exists()
    assert platform.storage.cache_dir().exists()
    assert platform.storage.state_dir().exists()


def test_native_deploy_ensures_user_key(xdg_dirs):
    """Test that NativePlatform.deploy() ensures user key exists."""
    platform = NativePlatform()

    result = platform.deploy()

    assert result is True
    assert platform.storage.user_key_path().exists()


def test_native_build_returns_true(xdg_dirs):
    """Test that NativePlatform.build() returns True (no build needed)."""
    platform = NativePlatform()

    # Native platform doesn't need building
    result = platform.build()

    assert result is True


def test_native_platform_service_lifecycle(xdg_dirs):
    """Test that NativePlatform can start and stop services."""
    platform = NativePlatform()

    # Should start without errors
    platform.start()
    assert platform._running

    # Should stop without errors
    platform.stop()
    assert not platform._running


def test_native_platform_logs():
    """Test native platform logs."""
    platform = NativePlatform()

    logs = platform.logs()

    assert isinstance(logs, str)
    assert "No logs available" in logs


def test_native_platform_status_not_deployed():
    """Test status when not deployed."""
    platform = NativePlatform()

    status = platform.status()
    assert status == "not deployed"


def test_native_platform_status_deployed(xdg_dirs):
    """Test status when deployed."""
    platform = NativePlatform()
    platform.deploy()

    status = platform.status()
    assert status in ["running", "stopped"]


def test_native_platform_info(xdg_dirs):
    """Test platform info."""
    platform = NativePlatform()
    platform.deploy()

    info = platform.info()
    assert info.runtime_type == "native"
    assert info.server_status in ["running", "stopped", "not deployed"]


def test_native_platform_du(xdg_dirs):
    """Test disk usage calculation."""
    platform = NativePlatform()
    platform.deploy()

    usage = platform.du()
    assert usage.config >= 0
    assert usage.install.data >= 0
    assert usage.mcp.repos >= 0


def test_native_platform_remove(xdg_dirs):
    """Test removing platform."""
    platform = NativePlatform()
    platform.deploy()

    # Create some files to remove
    install_dir = platform.storage.install_dir()
    install_dir.mkdir(parents=True, exist_ok=True)
    (install_dir / "test.txt").write_text("test")

    removed = platform.remove()
    assert len(removed) > 0
    assert not install_dir.exists()
