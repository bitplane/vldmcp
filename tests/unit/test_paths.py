"""Tests for the XDG paths module."""

import os
from pathlib import Path
from unittest.mock import patch


from vldmcp import paths


def test_config_dir_with_xdg():
    """Test config_dir returns XDG_CONFIG_HOME when set."""
    with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/config"}):
        assert paths.config_dir() == Path("/custom/config/vldmcp")


def test_config_dir_without_xdg():
    """Test config_dir returns default when XDG_CONFIG_HOME not set."""
    with patch.dict(os.environ, {}, clear=True):
        # Add HOME back
        with patch.dict(os.environ, {"HOME": "/home/testuser"}):
            assert paths.config_dir() == Path("/home/testuser/.config/vldmcp")


def test_data_dir_with_xdg():
    """Test data_dir returns XDG_DATA_HOME when set."""
    with patch.dict(os.environ, {"XDG_DATA_HOME": "/custom/data"}):
        assert paths.data_dir() == Path("/custom/data/vldmcp")


def test_data_dir_without_xdg():
    """Test data_dir returns default when XDG_DATA_HOME not set."""
    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {"HOME": "/home/testuser"}):
            assert paths.data_dir() == Path("/home/testuser/.local/share/vldmcp")


def test_state_dir_with_xdg():
    """Test state_dir returns XDG_STATE_HOME when set."""
    with patch.dict(os.environ, {"XDG_STATE_HOME": "/custom/state"}):
        assert paths.state_dir() == Path("/custom/state/vldmcp")


def test_state_dir_without_xdg():
    """Test state_dir returns default when XDG_STATE_HOME not set."""
    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {"HOME": "/home/testuser"}):
            assert paths.state_dir() == Path("/home/testuser/.local/state/vldmcp")


def test_cache_dir_with_xdg():
    """Test cache_dir returns XDG_CACHE_HOME when set."""
    with patch.dict(os.environ, {"XDG_CACHE_HOME": "/custom/cache"}):
        assert paths.cache_dir() == Path("/custom/cache/vldmcp")


def test_cache_dir_without_xdg():
    """Test cache_dir returns default when XDG_CACHE_HOME not set."""
    with patch.dict(os.environ, {}, clear=True):
        with patch.dict(os.environ, {"HOME": "/home/testuser"}):
            assert paths.cache_dir() == Path("/home/testuser/.cache/vldmcp")


def test_runtime_dir_with_xdg():
    """Test runtime_dir returns XDG_RUNTIME_DIR when set."""
    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": "/run/user/1000"}):
        assert paths.runtime_dir() == Path("/run/user/1000/vldmcp")


def test_runtime_dir_without_xdg():
    """Test runtime_dir returns fallback when XDG_RUNTIME_DIR not set."""
    with patch.dict(os.environ, {"USER": "testuser"}, clear=True):
        assert paths.runtime_dir() == Path("/tmp/vldmcp-testuser")


def test_user_key_path():
    """Test user_key_path returns correct path."""
    with patch.dict(os.environ, {"XDG_DATA_HOME": "/custom/data"}):
        assert paths.user_key_path() == Path("/custom/data/vldmcp/keys/user.key")


def test_node_dir():
    """Test node_dir returns correct path for a node ID."""
    with patch.dict(os.environ, {"XDG_STATE_HOME": "/custom/state"}):
        assert paths.node_dir("node123") == Path("/custom/state/vldmcp/nodes/node123")


def test_node_key_path():
    """Test node_key_path returns correct path for a node key."""
    with patch.dict(os.environ, {"XDG_STATE_HOME": "/custom/state"}):
        assert paths.node_key_path("node123") == Path("/custom/state/vldmcp/nodes/node123/key")


def test_repos_dir():
    """Test repos_dir returns correct path."""
    with patch.dict(os.environ, {"XDG_CACHE_HOME": "/custom/cache"}):
        assert paths.repos_dir() == Path("/custom/cache/vldmcp/src")


def test_build_dir():
    """Test build_dir returns correct path."""
    with patch.dict(os.environ, {"XDG_CACHE_HOME": "/custom/cache"}):
        assert paths.build_dir() == Path("/custom/cache/vldmcp/build")


def test_install_dir():
    """Test install_dir returns correct path."""
    with patch.dict(os.environ, {"XDG_DATA_HOME": "/custom/data"}):
        assert paths.install_dir() == Path("/custom/data/vldmcp/install")


def test_pid_file_path():
    """Test pid_file_path returns correct path."""
    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": "/run/user/1000"}):
        assert paths.pid_file_path() == Path("/run/user/1000/vldmcp/vldmcp.pid")


def test_create_directories(tmp_path):
    """Test create_directories creates all necessary directories."""
    with patch.dict(
        os.environ,
        {
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
            "XDG_DATA_HOME": str(tmp_path / "data"),
            "XDG_STATE_HOME": str(tmp_path / "state"),
            "XDG_CACHE_HOME": str(tmp_path / "cache"),
            "XDG_RUNTIME_DIR": str(tmp_path / "runtime"),
        },
    ):
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
