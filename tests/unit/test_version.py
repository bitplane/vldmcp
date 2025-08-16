"""Tests for version utilities."""

import subprocess
from unittest.mock import patch

from vldmcp.util.version import is_development, get_version, _git_describe
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


def test_git_describe_success():
    """Test _git_describe with successful git command."""
    with patch("subprocess.check_output") as mock_check:
        mock_check.return_value = "v0.1.0-5-g1234567\n"
        result = _git_describe()
        assert result == "v0.1.0-5-g1234567"
        mock_check.assert_called_once_with(
            ["git", "describe", "--dirty", "--always", "--tags"], stderr=subprocess.DEVNULL, text=True
        )


def test_git_describe_empty_output():
    """Test _git_describe with empty git output."""
    with patch("subprocess.check_output") as mock_check:
        mock_check.return_value = ""
        result = _git_describe()
        assert result is None


def test_git_describe_exception():
    """Test _git_describe when git command fails."""
    with patch("subprocess.check_output") as mock_check:
        mock_check.side_effect = subprocess.CalledProcessError(1, "git")
        result = _git_describe()
        assert result is None


def test_git_describe_file_not_found():
    """Test _git_describe when git is not installed."""
    with patch("subprocess.check_output") as mock_check:
        mock_check.side_effect = FileNotFoundError("git not found")
        result = _git_describe()
        assert result is None


def test_get_version_with_git_decoration():
    """Test get_version includes git info in development mode."""
    with (
        patch("vldmcp.util.version.is_development", return_value=True),
        patch("vldmcp.util.version._git_describe", return_value="v0.1.0-dirty"),
        patch("vldmcp.util.version.version", return_value="0.0.1"),
    ):
        version = get_version()
        assert version == "0.0.1+v0.1.0-dirty"


def test_get_version_git_same_as_base():
    """Test get_version when git version matches base version."""
    with (
        patch("vldmcp.util.version.is_development", return_value=True),
        patch("vldmcp.util.version._git_describe", return_value="0.0.1"),
        patch("vldmcp.util.version.version", return_value="0.0.1"),
    ):
        version = get_version()
        assert version == "0.0.1"


def test_get_version_no_git_info():
    """Test get_version when git info is not available."""
    with (
        patch("vldmcp.util.version.is_development", return_value=True),
        patch("vldmcp.util.version._git_describe", return_value=None),
        patch("vldmcp.util.version.version", return_value="0.0.1"),
    ):
        version = get_version()
        assert version == "0.0.1"


def test_get_version_not_development():
    """Test get_version in non-development mode."""
    with (
        patch("vldmcp.util.version.is_development", return_value=False),
        patch("vldmcp.util.version.version", return_value="1.0.0"),
    ):
        version = get_version()
        assert version == "1.0.0"


def test_is_development_no_git_dir(tmp_path):
    """Test is_development when no .git directory exists."""
    # Create a fake version.py file in temp directory structure
    fake_src = tmp_path / "src" / "vldmcp" / "util"
    fake_src.mkdir(parents=True)
    fake_file = fake_src / "version.py"
    fake_file.write_text("")

    # Mock __file__ to point to our temp file (no .git 3 levels up)
    with patch("vldmcp.util.version.__file__", str(fake_file)):
        assert is_development() is False
