"""Tests for server install command."""

import subprocess
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from vldmcp import paths
from vldmcp.cli.server import install


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
    with patch("vldmcp.server_manager.__version__", "1.2.3"):
        result = runner.invoke(install)

    assert result.exit_code == 0
    dockerfile = (paths.install_dir() / "base" / "Dockerfile").read_text()
    assert "pip install vldmcp==1.2.3" in dockerfile
    assert "FROM python:3.10-slim" in dockerfile
    assert 'CMD ["vldmcpd"]' in dockerfile


def test_install_clones_from_local_repo_if_available(tmp_path, monkeypatch):
    """Test that install clones from local repo when it exists."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()

    # Get the actual project root
    project_root = Path(__file__).parent.parent.parent.parent

    # Get current HEAD commit
    current_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project_root, capture_output=True, text=True
    ).stdout.strip()[:7]  # Use short commit hash

    # Patch __version__ to trigger git mode with real commit
    with patch("vldmcp.server_manager.__version__", f"1.2.3+{current_commit}"):
        result = runner.invoke(install)

    assert result.exit_code == 0

    # Check that repo was cloned
    repo_dir = paths.repos_dir() / "vldmcp"
    assert repo_dir.exists()
    assert (repo_dir / ".git").exists()

    # Verify it's actually a git repo
    result = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=repo_dir, capture_output=True, text=True)
    assert result.returncode == 0

    # Check Dockerfile was created correctly
    dockerfile = (paths.install_dir() / "base" / "Dockerfile").read_text()
    assert "COPY repo /app" in dockerfile
    assert "pip install -e ." in dockerfile
    assert 'CMD ["vldmcpd"]' in dockerfile


def test_install_updates_existing_repo(tmp_path, monkeypatch):
    """Test that install updates existing repository."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()

    # Get current HEAD commit
    project_root = Path(__file__).parent.parent.parent.parent
    current_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project_root, capture_output=True, text=True
    ).stdout.strip()[:7]

    # First install to clone the repo
    with patch("vldmcp.server_manager.__version__", f"1.2.3+{current_commit}"):
        result = runner.invoke(install)
        assert result.exit_code == 0

    repo_dir = paths.repos_dir() / "vldmcp"
    assert repo_dir.exists()

    # Get initial commit
    subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_dir, capture_output=True, text=True).stdout.strip()

    # Run install again - should update (using same commit, but tests the update path)
    with patch("vldmcp.server_manager.__version__", f"1.2.3+{current_commit}"):
        result = runner.invoke(install)
        assert result.exit_code == 0

    # Verify repo still exists and is valid
    assert (repo_dir / ".git").exists()

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
    with patch("vldmcp.server_manager.__version__", "1.2.3"):
        result = runner.invoke(install)

    assert result.exit_code == 0

    # Should create repo dir even for PyPI install
    assert (paths.repos_dir() / "vldmcp").exists()

    # Check Dockerfile uses pip install
    dockerfile = (paths.install_dir() / "base" / "Dockerfile").read_text()
    assert "pip install vldmcp==1.2.3" in dockerfile
    assert "COPY repo" not in dockerfile
    assert "git clone" not in dockerfile
    assert 'CMD ["vldmcpd"]' in dockerfile
