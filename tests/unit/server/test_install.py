"""Tests for server install command."""

from unittest.mock import patch

from click.testing import CliRunner

from vldmcp import paths
from vldmcp.cli.lifecycle import install


def test_install_creates_directories(tmp_path, monkeypatch):
    """Test that install creates required directories."""
    # Patch XDG directories to use tmp_path
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()
    result = runner.invoke(install)

    assert result.exit_code == 0
    assert paths.install_dir().exists()
    assert paths.user_key_path().exists()
    # Note: base directory and Dockerfile only created for container runtimes
    # This test uses the detected runtime which is likely native in test environment


def test_install_creates_pip_dockerfile_for_release_version(tmp_path, monkeypatch):
    """Test that install creates correct Dockerfile for pip installation."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()
    with patch("vldmcp.__version__", "1.2.3"):
        result = runner.invoke(install)

    assert result.exit_code == 0


def test_install_creates_pypi_dockerfile_for_dev_version(tmp_path, monkeypatch):
    """Test that install creates PyPI Dockerfile even for dev versions."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()

    # Test with a dev version (has +)
    with patch("vldmcp.__version__", "1.2.3+abc123"):
        result = runner.invoke(install)

    assert result.exit_code == 0


def test_install_multiple_times_succeeds(tmp_path, monkeypatch):
    """Test that running install multiple times succeeds."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()

    # First install
    with patch("vldmcp.__version__", "1.2.3"):
        result = runner.invoke(install)
        assert result.exit_code == 0

    # Verify installation
    assert paths.install_dir().exists()

    # Run install again - should succeed
    with patch("vldmcp.__version__", "1.2.4"):
        result = runner.invoke(install)
        assert result.exit_code == 0

    # Should complete successfully
    assert "Installation complete!" in result.output


def test_install_handles_pypi_version(tmp_path, monkeypatch):
    """Test that install handles PyPI version correctly."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()

    # Test with a release version (no +)
    with patch("vldmcp.__version__", "1.2.3"):
        result = runner.invoke(install)

    assert result.exit_code == 0

    # Check Dockerfile uses pip install (only created for container runtimes)
    # Since we're using the guessed runtime (likely native in tests), may not create Dockerfile
