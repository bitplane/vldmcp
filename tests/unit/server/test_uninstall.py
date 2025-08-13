"""Tests for server uninstall command."""

from click.testing import CliRunner

from vldmcp import paths
from vldmcp.cli.server import uninstall


def test_uninstall_removes_directory(tmp_path, monkeypatch):
    """Test that uninstall removes the vldmcp directories."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()

    # Create some directories to remove
    install_dir = paths.install_dir()
    cache_dir = paths.cache_dir()
    install_dir.mkdir(parents=True)
    cache_dir.mkdir(parents=True)
    (install_dir / "test.txt").write_text("test content")

    assert install_dir.exists()
    assert cache_dir.exists()

    result = runner.invoke(uninstall, ["--yes"])

    assert result.exit_code == 0
    assert not install_dir.exists()
    assert not cache_dir.exists()
    assert "Uninstallation complete!" in result.output


def test_uninstall_with_y_flag_removes_directory(tmp_path, monkeypatch):
    """Test that uninstall with -y flag removes the directory without prompting."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()

    install_dir = paths.install_dir()
    install_dir.mkdir(parents=True)

    result = runner.invoke(uninstall, ["-y"])

    assert result.exit_code == 0
    assert not install_dir.exists()
    assert "Uninstallation complete!" in result.output


def test_uninstall_prompts_without_yes_flag(tmp_path, monkeypatch):
    """Test that uninstall prompts for confirmation without --yes flag."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()

    install_dir = paths.install_dir()
    install_dir.mkdir(parents=True)

    # Test aborting (user types 'n')
    result = runner.invoke(uninstall, [], input="n\n")

    assert result.exit_code == 1  # Aborted
    assert install_dir.exists()  # Directory still exists
    assert "Continue?" in result.output


def test_uninstall_confirms_removal_with_prompt(tmp_path, monkeypatch):
    """Test that uninstall removes directory when user confirms."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()

    install_dir = paths.install_dir()
    install_dir.mkdir(parents=True)

    # Test confirming (user types 'y')
    result = runner.invoke(uninstall, [], input="y\n")

    assert result.exit_code == 0
    assert not install_dir.exists()
    assert "Uninstallation complete!" in result.output


def test_uninstall_handles_missing_installation(tmp_path, monkeypatch):
    """Test that uninstall handles missing installation gracefully."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()

    # No vldmcp directories exist
    result = runner.invoke(uninstall, ["--yes"])

    assert result.exit_code == 0
    assert "No vldmcp installation found." in result.output


def test_uninstall_removes_nested_content(tmp_path, monkeypatch):
    """Test that uninstall removes all nested directories and files."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()

    # Create nested structure
    install_dir = paths.install_dir()
    cache_dir = paths.cache_dir()
    (install_dir / "base" / "subdir").mkdir(parents=True)
    (cache_dir / "repo" / ".git").mkdir(parents=True)
    (install_dir / "base" / "Dockerfile").write_text("FROM python:3.10")
    (cache_dir / "repo" / "README.md").write_text("# Test")

    assert install_dir.exists()
    assert (install_dir / "base" / "Dockerfile").exists()

    result = runner.invoke(uninstall, ["-y"])

    assert result.exit_code == 0
    assert not install_dir.exists()
    assert not cache_dir.exists()
    assert "Uninstallation complete!" in result.output


def test_uninstall_with_purge_removes_all_data(tmp_path, monkeypatch):
    """Test that uninstall with --purge removes all data including keys."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()

    # Create all directories
    install_dir = paths.install_dir()
    cache_dir = paths.cache_dir()
    config_dir = paths.config_dir()
    data_dir = paths.data_dir()
    state_dir = paths.state_dir()

    for d in [install_dir, cache_dir, config_dir, data_dir, state_dir]:
        d.mkdir(parents=True, exist_ok=True)
        (d / "test.txt").write_text("test")

    # Test with purge
    result = runner.invoke(uninstall, ["--purge", "--yes"])

    assert result.exit_code == 0
    assert not install_dir.exists()
    assert not cache_dir.exists()
    assert not config_dir.exists()
    assert not data_dir.exists()
    assert not state_dir.exists()
    assert "WARNING: --purge will remove your identity keys!" in result.output
    assert "Uninstallation complete!" in result.output


def test_uninstall_without_purge_keeps_keys(tmp_path, monkeypatch):
    """Test that uninstall without --purge keeps user keys and config."""
    # Patch XDG directories
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = CliRunner()

    # Create directories
    install_dir = paths.install_dir()
    cache_dir = paths.cache_dir()
    config_dir = paths.config_dir()
    data_dir = paths.data_dir()

    for d in [install_dir, cache_dir, config_dir, data_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Create user key
    user_key_path = paths.user_key_path()
    user_key_path.parent.mkdir(parents=True, exist_ok=True)
    user_key_path.write_bytes(b"secret_key")

    # Run uninstall without purge
    result = runner.invoke(uninstall, ["--yes"])

    assert result.exit_code == 0
    assert not install_dir.exists()  # Install data removed
    assert not cache_dir.exists()  # Cache removed
    assert config_dir.exists()  # Config kept
    assert data_dir.exists()  # Data kept
    assert user_key_path.exists()  # User key kept
    assert "Uninstallation complete!" in result.output
    assert "WARNING: --purge will remove your identity keys!" not in result.output
