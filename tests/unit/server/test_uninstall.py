"""Tests for server uninstall command."""

from click.testing import CliRunner

from vldmcp.cli.server import uninstall


def test_uninstall_with_yes_flag_removes_directory(tmp_path):
    """Test that uninstall with --yes flag removes the directory without prompting."""
    runner = CliRunner()
    prefix = tmp_path / "test_prefix"
    vldmcp_dir = prefix / "vldmcp"
    vldmcp_dir.mkdir(parents=True)

    # Create some dummy content
    (vldmcp_dir / "test_file.txt").write_text("test content")
    assert vldmcp_dir.exists()

    result = runner.invoke(uninstall, ["--prefix", str(prefix), "--yes"])

    assert result.exit_code == 0
    assert not vldmcp_dir.exists()
    assert "Uninstallation complete!" in result.output


def test_uninstall_with_y_flag_removes_directory(tmp_path):
    """Test that uninstall with -y flag removes the directory without prompting."""
    runner = CliRunner()
    prefix = tmp_path / "test_prefix"
    vldmcp_dir = prefix / "vldmcp"
    vldmcp_dir.mkdir(parents=True)

    result = runner.invoke(uninstall, ["--prefix", str(prefix), "-y"])

    assert result.exit_code == 0
    assert not vldmcp_dir.exists()
    assert "Uninstallation complete!" in result.output


def test_uninstall_prompts_without_yes_flag(tmp_path):
    """Test that uninstall prompts for confirmation without --yes flag."""
    runner = CliRunner()
    prefix = tmp_path / "test_prefix"
    vldmcp_dir = prefix / "vldmcp"
    vldmcp_dir.mkdir(parents=True)

    # Test aborting (user types 'n')
    result = runner.invoke(uninstall, ["--prefix", str(prefix)], input="n\n")

    assert result.exit_code == 1  # Aborted
    assert vldmcp_dir.exists()  # Directory should still exist
    assert "This will remove" in result.output
    assert "Continue?" in result.output


def test_uninstall_confirms_removal_with_prompt(tmp_path):
    """Test that uninstall removes directory when user confirms."""
    runner = CliRunner()
    prefix = tmp_path / "test_prefix"
    vldmcp_dir = prefix / "vldmcp"
    vldmcp_dir.mkdir(parents=True)

    # Test confirming (user types 'y')
    result = runner.invoke(uninstall, ["--prefix", str(prefix)], input="y\n")

    assert result.exit_code == 0
    assert not vldmcp_dir.exists()  # Directory should be removed
    assert "Uninstallation complete!" in result.output


def test_uninstall_handles_missing_installation(tmp_path):
    """Test that uninstall handles missing installation gracefully."""
    runner = CliRunner()
    prefix = tmp_path / "test_prefix"

    # No vldmcp directory exists
    result = runner.invoke(uninstall, ["--prefix", str(prefix), "--yes"])

    assert result.exit_code == 0
    assert "No vldmcp installation found." in result.output
    assert "Uninstallation complete!" not in result.output


def test_uninstall_removes_nested_content(tmp_path):
    """Test that uninstall removes all nested directories and files."""
    runner = CliRunner()
    prefix = tmp_path / "test_prefix"
    vldmcp_dir = prefix / "vldmcp"

    # Create nested structure
    (vldmcp_dir / "base" / "subdir").mkdir(parents=True)
    (vldmcp_dir / "repo" / ".git").mkdir(parents=True)
    (vldmcp_dir / "base" / "Dockerfile").write_text("FROM python:3.10")
    (vldmcp_dir / "repo" / "README.md").write_text("# Test")

    assert vldmcp_dir.exists()
    assert (vldmcp_dir / "base" / "Dockerfile").exists()

    result = runner.invoke(uninstall, ["--prefix", str(prefix), "-y"])

    assert result.exit_code == 0
    assert not vldmcp_dir.exists()
    assert not (prefix / "vldmcp").exists()  # Ensure completely gone
