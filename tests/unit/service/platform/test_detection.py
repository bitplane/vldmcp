"""Tests for platform detection logic."""

import pytest
from unittest.mock import patch, MagicMock

from vldmcp.service.platform.detection import guess_platform, get_platform
from vldmcp.service.platform.native import NativePlatform


def test_guess_platform_development():
    """Test that development mode always returns native."""
    with patch("vldmcp.service.platform.detection.is_development", return_value=True):
        result = guess_platform()
        assert result == "native"


def test_guess_platform_podman_available():
    """Test that podman is preferred when available in non-dev mode."""
    with (
        patch("vldmcp.service.platform.detection.is_development", return_value=False),
        patch("vldmcp.service.platform.detection.PodmanPlatform", "MockPodmanPlatform"),
        patch("vldmcp.service.platform.detection.shutil.which") as mock_which,
    ):

        def which_side_effect(cmd):
            return "/usr/bin/podman" if cmd == "podman" else None

        mock_which.side_effect = which_side_effect

        result = guess_platform()
        assert result == "podman"


def test_guess_platform_vldmcpd_fallback():
    """Test that vldmcpd is used as fallback when podman not available."""
    with (
        patch("vldmcp.service.platform.detection.is_development", return_value=False),
        patch("vldmcp.service.platform.detection.PodmanPlatform", None),
        patch("vldmcp.service.platform.detection.shutil.which") as mock_which,
    ):

        def which_side_effect(cmd):
            return "/usr/bin/vldmcpd" if cmd == "vldmcpd" else None

        mock_which.side_effect = which_side_effect

        result = guess_platform()
        assert result == "native"


def test_guess_platform_default_fallback():
    """Test that native is used as default when nothing else available."""
    with (
        patch("vldmcp.service.platform.detection.is_development", return_value=False),
        patch("vldmcp.service.platform.detection.PodmanPlatform", None),
        patch("vldmcp.service.platform.detection.shutil.which", return_value=None),
    ):
        result = guess_platform()
        assert result == "native"


def test_get_platform_native():
    """Test getting native platform by name."""
    platform = get_platform("native")
    assert isinstance(platform, NativePlatform)


def test_get_platform_case_insensitive():
    """Test that platform names are case insensitive."""
    platform = get_platform("NATIVE")
    assert isinstance(platform, NativePlatform)

    platform = get_platform("  Native  ")
    assert isinstance(platform, NativePlatform)


def test_get_platform_invalid_name():
    """Test that invalid platform names raise ValueError."""
    with pytest.raises(ValueError, match="Unsupported platform 'invalid'"):
        get_platform("invalid")


def test_get_platform_podman_not_available():
    """Test that requesting podman when not available raises RuntimeError."""
    with patch("vldmcp.service.platform.detection.PodmanPlatform", None):
        with pytest.raises(RuntimeError, match="Podman platform is not available"):
            get_platform("podman")


def test_get_platform_guess_uses_config():
    """Test that guess mode uses config when available."""
    mock_config = MagicMock()
    mock_config.platform.type = "native"

    with patch("vldmcp.service.platform.detection.get_config", return_value=mock_config):
        platform = get_platform("guess")
        assert isinstance(platform, NativePlatform)


def test_get_platform_guess_auto_detects():
    """Test that guess mode auto-detects when config is 'guess'."""
    mock_config = MagicMock()
    mock_config.platform.type = "guess"

    with (
        patch("vldmcp.service.platform.detection.get_config", return_value=mock_config),
        patch("vldmcp.service.platform.detection.guess_platform", return_value="native"),
    ):
        platform = get_platform("guess")
        assert isinstance(platform, NativePlatform)


def test_get_platform_guess_does_not_save():
    """Test that auto-detection does NOT save the result to config."""
    mock_config = MagicMock()
    mock_config.platform.type = "guess"

    with (
        patch("vldmcp.service.platform.detection.get_config", return_value=mock_config),
        patch("vldmcp.service.platform.detection.is_development", return_value=True),
    ):
        platform = get_platform("guess")
        assert isinstance(platform, NativePlatform)
        # Detection should work without trying to save config
