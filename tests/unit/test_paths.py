"""Tests for the XDG paths module."""

from pathlib import Path

from vldmcp import paths


def test_config_dir_with_xdg(monkeypatch):
    """Test config_dir returns XDG_CONFIG_HOME when set."""
    monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")
    assert paths.config_dir() == Path("/custom/config/vldmcp")


def test_config_dir_without_xdg(monkeypatch):
    """Test config_dir returns default when XDG_CONFIG_HOME not set."""
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", "/home/testuser")
    assert paths.config_dir() == Path("/home/testuser/.config/vldmcp")


def test_data_dir_with_xdg(monkeypatch):
    """Test data_dir returns XDG_DATA_HOME when set."""
    monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")
    assert paths.data_dir() == Path("/custom/data/vldmcp")


def test_data_dir_without_xdg(monkeypatch):
    """Test data_dir returns default when XDG_DATA_HOME not set."""
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setenv("HOME", "/home/testuser")
    assert paths.data_dir() == Path("/home/testuser/.local/share/vldmcp")


def test_state_dir_with_xdg(monkeypatch):
    """Test state_dir returns XDG_STATE_HOME when set."""
    monkeypatch.setenv("XDG_STATE_HOME", "/custom/state")
    assert paths.state_dir() == Path("/custom/state/vldmcp")


def test_state_dir_without_xdg(monkeypatch):
    """Test state_dir returns default when XDG_STATE_HOME not set."""
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    monkeypatch.setenv("HOME", "/home/testuser")
    assert paths.state_dir() == Path("/home/testuser/.local/state/vldmcp")


def test_cache_dir_with_xdg(monkeypatch):
    """Test cache_dir returns XDG_CACHE_HOME when set."""
    monkeypatch.setenv("XDG_CACHE_HOME", "/custom/cache")
    assert paths.cache_dir() == Path("/custom/cache/vldmcp")


def test_cache_dir_without_xdg(monkeypatch):
    """Test cache_dir returns default when XDG_CACHE_HOME not set."""
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    monkeypatch.setenv("HOME", "/home/testuser")
    assert paths.cache_dir() == Path("/home/testuser/.cache/vldmcp")


def test_runtime_dir_with_xdg(monkeypatch):
    """Test runtime_dir returns XDG_RUNTIME_DIR when set."""
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1000")
    assert paths.runtime_dir() == Path("/run/user/1000/vldmcp")


def test_runtime_dir_without_xdg(monkeypatch):
    """Test runtime_dir returns fallback when XDG_RUNTIME_DIR not set."""
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    monkeypatch.setenv("USER", "testuser")
    assert paths.runtime_dir() == Path("/tmp/vldmcp-testuser")


def test_user_key_path(monkeypatch):
    """Test user_key_path returns correct path."""
    monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")
    assert paths.user_key_path() == Path("/custom/data/vldmcp/keys/user.key")


def test_node_dir(monkeypatch):
    """Test node_dir returns correct path for a node ID."""
    monkeypatch.setenv("XDG_STATE_HOME", "/custom/state")
    assert paths.node_dir("node123") == Path("/custom/state/vldmcp/nodes/node123")


def test_node_key_path(monkeypatch):
    """Test node_key_path returns correct path for a node key."""
    monkeypatch.setenv("XDG_STATE_HOME", "/custom/state")
    assert paths.node_key_path("node123") == Path("/custom/state/vldmcp/nodes/node123/key")


def test_repos_dir(monkeypatch):
    """Test repos_dir returns correct path."""
    monkeypatch.setenv("XDG_CACHE_HOME", "/custom/cache")
    assert paths.repos_dir() == Path("/custom/cache/vldmcp/src")


def test_build_dir(monkeypatch):
    """Test build_dir returns correct path."""
    monkeypatch.setenv("XDG_CACHE_HOME", "/custom/cache")
    assert paths.build_dir() == Path("/custom/cache/vldmcp/build")


def test_install_dir(monkeypatch):
    """Test install_dir returns correct path."""
    monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")
    assert paths.install_dir() == Path("/custom/data/vldmcp/install")


def test_pid_file_path(monkeypatch):
    """Test pid_file_path returns correct path."""
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1000")
    assert paths.pid_file_path() == Path("/run/user/1000/vldmcp/vldmcp.pid")


def test_create_directories(xdg_dirs):
    """Test create_directories creates all necessary directories."""
    paths.create_directories()

    # Check directories exist
    assert paths.config_dir().exists()
    assert paths.data_dir().exists()
    assert paths.state_dir().exists()
    assert paths.cache_dir().exists()
    assert paths.runtime_dir().exists()
    assert paths.repos_dir().exists()
    assert paths.build_dir().exists()
    assert paths.install_dir().exists()

    # Check secure directories have correct permissions
    keys_dir = paths.data_dir() / "keys"
    assert keys_dir.exists()
    assert oct(keys_dir.stat().st_mode)[-3:] == "700"

    assert oct(paths.state_dir().stat().st_mode)[-3:] == "700"
    assert oct(paths.runtime_dir().stat().st_mode)[-3:] == "700"
