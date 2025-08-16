"""Tests for version utilities."""

from vldmcp.util.version import is_development, get_version
from vldmcp.service.platform.detection import get_platform, guess_platform
from vldmcp.service.platform.native import NativePlatform


def test_is_development():
    """Test development detection."""
    # In our test environment, we should be in development mode
    assert is_development() is True


def test_get_version():
    """Test version string generation."""
    version = get_version()
    assert isinstance(version, str)
    assert len(version) > 0
    # Should contain base version
    assert "0.0.1" in version


def test_get_version_with_custom_dist():
    """Test version with custom distribution name."""
    version = get_version("nonexistent-package")
    # Should fall back to 0.0.0 for nonexistent package
    assert version.startswith("0.0.0")


def test_platform_detection_uses_native_in_tests():
    """Test that platform detection uses native mode in test environment."""
    # Since we're in a development environment (git repo), should use native
    assert is_development() is True
    assert guess_platform() == "native"

    # get_platform() should return NativePlatform instance
    platform = get_platform()
    assert isinstance(platform, NativePlatform)
    assert type(platform).__name__ == "NativePlatform"
