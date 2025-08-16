"""Unit tests for NativeBackend install functionality."""

from vldmcp.runtime import NativeBackend
from vldmcp import paths


def test_native_install_creates_directories(xdg_dirs):
    """Test that NativeBackend.install() creates required directories."""
    backend = NativeBackend()

    # Run install
    result = backend.install()

    assert result is True
    assert paths.data_dir().exists()
    assert paths.config_dir().exists()
    assert paths.state_dir().exists()
    assert paths.cache_dir().exists()
    assert paths.runtime_dir().exists()
    assert paths.user_key_path().exists()


def test_native_install_preserves_existing_key(xdg_dirs):
    """Test that NativeBackend.install() preserves existing user key."""
    backend = NativeBackend()

    # Create a key file first
    key_path = paths.user_key_path()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    test_key = b"test_key_content_32_bytes_exactly!" * 1  # 34 bytes, but we'll trim
    test_key = test_key[:32]  # Make it exactly 32 bytes
    key_path.write_bytes(test_key)

    # Run install
    result = backend.install()

    assert result is True
    assert key_path.exists()
    # Verify key wasn't changed
    assert key_path.read_bytes() == test_key


def test_native_install_idempotent(xdg_dirs):
    """Test that NativeBackend.install() can be run multiple times."""
    backend = NativeBackend()

    # First install
    result1 = backend.install()
    assert result1 is True

    # Get the key that was created
    key_path = paths.user_key_path()
    original_key = key_path.read_bytes()

    # Second install - should succeed and not change the key
    result2 = backend.install()
    assert result2 is True
    assert key_path.read_bytes() == original_key


def test_native_deploy_calls_install(xdg_dirs):
    """Test that NativeBackend.deploy() calls install."""
    backend = NativeBackend()

    # deploy should call install() and build_if_needed()
    result = backend.deploy()

    assert result is True
    assert paths.user_key_path().exists()


def test_native_build_if_needed_returns_true(xdg_dirs):
    """Test that NativeBackend.build_if_needed() returns True (no build needed)."""
    backend = NativeBackend()

    # Native backend doesn't need building
    result = backend.build_if_needed()

    assert result is True
