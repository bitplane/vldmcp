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
    assert (paths.install_dir() / "base").exists()
    assert (paths.install_dir() / "base" / "Dockerfile").exists()
    assert paths.user_key_path().exists()


def test_install_creates_pip_dockerfile_for_release_version(tmp_path, monkeypatch):
    """Test that install creates correct Dockerfile for pip installation."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()
    with patch("vldmcp.deployment.__version__", "1.2.3"):
        result = runner.invoke(install)

    assert result.exit_code == 0
    dockerfile = (paths.install_dir() / "base" / "Dockerfile").read_text()
    assert "pip install vldmcp==1.2.3" in dockerfile
    assert "FROM python:3.10-slim" in dockerfile
    assert 'CMD ["vldmcpd"]' in dockerfile


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
    with patch("vldmcp.deployment.__version__", "1.2.3+abc123"):
        result = runner.invoke(install)

    assert result.exit_code == 0

    # Check Dockerfile was created correctly - should still use PyPI
    dockerfile = (paths.install_dir() / "base" / "Dockerfile").read_text()
    assert "pip install vldmcp==1.2.3+abc123" in dockerfile
    assert "FROM python:3.10-slim" in dockerfile
    assert 'CMD ["vldmcpd"]' in dockerfile
    # Should NOT have git-related commands
    assert "COPY repo" not in dockerfile
    assert "pip install -e ." not in dockerfile


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
    with patch("vldmcp.deployment.__version__", "1.2.3"):
        result = runner.invoke(install)
        assert result.exit_code == 0

    # Verify installation
    assert paths.install_dir().exists()
    dockerfile_path = paths.install_dir() / "base" / "Dockerfile"
    assert dockerfile_path.exists()

    # Run install again - should succeed
    with patch("vldmcp.deployment.__version__", "1.2.4"):
        result = runner.invoke(install)
        assert result.exit_code == 0

    # Should complete successfully and update version
    assert "Installation complete!" in result.output
    dockerfile = dockerfile_path.read_text()
    assert "pip install vldmcp==1.2.4" in dockerfile


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
    with patch("vldmcp.deployment.__version__", "1.2.3"):
        result = runner.invoke(install)

    assert result.exit_code == 0

    # Check Dockerfile uses pip install
    dockerfile = (paths.install_dir() / "base" / "Dockerfile").read_text()
    assert "pip install vldmcp==1.2.3" in dockerfile
    assert "COPY repo" not in dockerfile
    assert "git clone" not in dockerfile
    assert 'CMD ["vldmcpd"]' in dockerfile
