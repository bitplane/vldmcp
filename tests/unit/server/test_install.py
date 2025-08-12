"""Tests for server install command."""

import subprocess
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from vldmcp.cli.server import install


def test_install_creates_directories(tmp_path):
    """Test that install creates required directories."""
    runner = CliRunner()
    prefix = tmp_path / "test_prefix"

    result = runner.invoke(install, ["--prefix", str(prefix)])

    assert result.exit_code == 0
    assert (prefix / "vldmcp" / "base").exists()
    assert (prefix / "vldmcp" / "repo").exists()  # Created even for PyPI install
    assert (prefix / "vldmcp" / "base" / "Dockerfile").exists()


def test_install_creates_pip_dockerfile_for_release_version(tmp_path):
    """Test that install creates correct Dockerfile for pip installation."""
    runner = CliRunner()
    prefix = tmp_path / "test_prefix"

    with patch("vldmcp.cli.server.__version__", "1.2.3"):
        result = runner.invoke(install, ["--prefix", str(prefix)])

    assert result.exit_code == 0
    dockerfile = (prefix / "vldmcp" / "base" / "Dockerfile").read_text()
    assert "pip install vldmcp==1.2.3" in dockerfile
    assert "FROM python:3.10-slim" in dockerfile


def test_install_clones_from_local_repo_if_available(tmp_path, monkeypatch):
    """Test that install clones from local repo when it exists."""
    runner = CliRunner()
    prefix = tmp_path / "test_prefix"

    # Get the actual project root
    project_root = Path(__file__).parent.parent.parent.parent

    # Get current HEAD commit
    current_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project_root, capture_output=True, text=True
    ).stdout.strip()[:7]  # Use short commit hash

    # Patch __version__ to trigger git mode with real commit
    with patch("vldmcp.cli.server.__version__", f"1.2.3+{current_commit}"):
        result = runner.invoke(install, ["--prefix", str(prefix)])

    assert result.exit_code == 0

    # Check that repo was cloned
    repo_dir = prefix / "vldmcp" / "repo"
    assert repo_dir.exists()
    assert (repo_dir / ".git").exists()

    # Verify it's actually a git repo
    result = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=repo_dir, capture_output=True, text=True)
    assert result.returncode == 0

    # Check Dockerfile was created correctly
    dockerfile = (prefix / "vldmcp" / "base" / "Dockerfile").read_text()
    assert "COPY repo /app" in dockerfile
    assert "pip install -e ." in dockerfile


def test_install_updates_existing_repo(tmp_path):
    """Test that install updates existing repository."""
    runner = CliRunner()
    prefix = tmp_path / "test_prefix"

    # Get current HEAD commit
    project_root = Path(__file__).parent.parent.parent.parent
    current_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project_root, capture_output=True, text=True
    ).stdout.strip()[:7]

    # First install to clone the repo
    with patch("vldmcp.cli.server.__version__", f"1.2.3+{current_commit}"):
        result = runner.invoke(install, ["--prefix", str(prefix)])
        assert result.exit_code == 0

    repo_dir = prefix / "vldmcp" / "repo"
    assert repo_dir.exists()

    # Get initial commit
    subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_dir, capture_output=True, text=True).stdout.strip()

    # Run install again - should update (using same commit, but tests the update path)
    with patch("vldmcp.cli.server.__version__", f"1.2.3+{current_commit}"):
        result = runner.invoke(install, ["--prefix", str(prefix)])
        assert result.exit_code == 0

    # Verify repo still exists and is valid
    assert (repo_dir / ".git").exists()

    # Should have fetched updates
    assert "Repository updated" in result.output or "Repository cloned" in result.output


def test_install_handles_pypi_version(tmp_path):
    """Test that install handles PyPI version correctly."""
    runner = CliRunner()
    prefix = tmp_path / "test_prefix"

    # Test with a release version (no +)
    with patch("vldmcp.cli.server.__version__", "1.2.3"):
        result = runner.invoke(install, ["--prefix", str(prefix)])

    assert result.exit_code == 0

    # Should create repo dir even for PyPI install
    assert (prefix / "vldmcp" / "repo").exists()

    # Check Dockerfile uses pip install
    dockerfile = (prefix / "vldmcp" / "base" / "Dockerfile").read_text()
    assert "pip install vldmcp==1.2.3" in dockerfile
    assert "COPY repo" not in dockerfile
    assert "git clone" not in dockerfile
