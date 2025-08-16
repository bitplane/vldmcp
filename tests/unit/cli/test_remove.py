"""Tests for the remove command."""

import click.testing

from vldmcp.cli import cli


def test_remove_with_purge_on_clean_system(tmp_path, monkeypatch):
    """Test that remove --purge --yes works even when nothing exists."""
    # Set up XDG dirs to tmp location
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = click.testing.CliRunner()

    # First remove should show message about nothing to remove
    result = runner.invoke(cli, ["server", "remove", "--purge", "--yes"])
    assert result.exit_code == 0
    assert "No vldmcp installation found" in result.output

    # Second remove should also work
    result = runner.invoke(cli, ["server", "remove", "--purge", "--yes"])
    assert result.exit_code == 0
    assert "No vldmcp installation found" in result.output


def test_remove_after_deploy(tmp_path, monkeypatch):
    """Test that remove works after deployment."""
    # Set up XDG dirs to tmp location
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = click.testing.CliRunner()

    # Deploy first
    result = runner.invoke(cli, ["server", "deploy"])
    assert result.exit_code == 0

    # Check that identity was created
    data_dir = tmp_path / "data" / "vldmcp"
    assert (data_dir / "keys" / "user.key").exists()

    # Remove without config/purge
    result = runner.invoke(cli, ["server", "remove", "--yes"])
    assert result.exit_code == 0

    # Identity should still exist
    assert (data_dir / "keys" / "user.key").exists()

    # Config should still exist
    config_dir = tmp_path / "config" / "vldmcp"
    assert config_dir.exists()


def test_remove_with_config_preserves_identity(tmp_path, monkeypatch):
    """Test that remove --config preserves identity keys."""
    # Set up XDG dirs to tmp location
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = click.testing.CliRunner()

    # Deploy first
    result = runner.invoke(cli, ["server", "deploy"])
    assert result.exit_code == 0

    # Save the original key
    key_path = tmp_path / "data" / "vldmcp" / "keys" / "user.key"
    original_key = key_path.read_bytes()

    # Remove with --config
    result = runner.invoke(cli, ["server", "remove", "--config", "--yes"])
    assert result.exit_code == 0

    # Identity should still exist and be unchanged
    assert key_path.exists()
    assert key_path.read_bytes() == original_key

    # Config should be gone
    config_dir = tmp_path / "config" / "vldmcp"
    assert not config_dir.exists()


def test_remove_with_purge_removes_everything(tmp_path, monkeypatch):
    """Test that remove --purge removes everything including identity."""
    # Set up XDG dirs to tmp location
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = click.testing.CliRunner()

    # Deploy first
    result = runner.invoke(cli, ["server", "deploy"])
    assert result.exit_code == 0

    # Remove with --purge
    result = runner.invoke(cli, ["server", "remove", "--purge", "--yes"])
    assert result.exit_code == 0
    assert "user data" in result.output.lower()

    # Everything should be gone
    assert not (tmp_path / "data" / "vldmcp").exists()
    assert not (tmp_path / "config" / "vldmcp").exists()
    assert not (tmp_path / "state" / "vldmcp").exists()
    assert not (tmp_path / "cache" / "vldmcp").exists()


def test_deploy_preserves_existing_identity(tmp_path, monkeypatch):
    """Test that deploy preserves existing identity keys."""
    # Set up XDG dirs to tmp location
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = click.testing.CliRunner()

    # First deploy
    result = runner.invoke(cli, ["server", "deploy"])
    assert result.exit_code == 0

    # Save the original key
    key_path = tmp_path / "data" / "vldmcp" / "keys" / "user.key"
    original_key = key_path.read_bytes()

    # Remove without purge (keeping identity)
    result = runner.invoke(cli, ["server", "remove", "--config", "--yes"])
    assert result.exit_code == 0
    assert key_path.exists()

    # Deploy again - should preserve existing key
    result = runner.invoke(cli, ["server", "deploy"])
    assert result.exit_code == 0
    assert "Using existing identity" in result.output

    # Key should be unchanged
    assert key_path.read_bytes() == original_key


def test_deploy_after_partial_remove(tmp_path, monkeypatch):
    """Test that deploy works after partial remove."""
    # Set up XDG dirs to tmp location
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    runner = click.testing.CliRunner()

    # First deploy
    result = runner.invoke(cli, ["server", "deploy"])
    assert result.exit_code == 0

    # Partial remove (no config/purge)
    result = runner.invoke(cli, ["server", "remove", "--yes"])
    assert result.exit_code == 0

    # Deploy again - should work
    result = runner.invoke(cli, ["server", "deploy"])
    assert result.exit_code == 0
    assert "Using existing identity" in result.output
