"""Tests for seed phrase functionality in server install command."""

from unittest.mock import patch
from click.testing import CliRunner

from vldmcp import paths, crypto
from vldmcp.cli.lifecycle import install, export_seed


def test_install_with_show_seed(xdg_dirs):
    """Test install with --show-seed flag displays mnemonic."""
    runner = CliRunner()

    # Mock the confirmation prompt to automatically say yes
    with patch("click.confirm", return_value=True):
        result = runner.invoke(install, ["--show-seed"])

    assert result.exit_code == 0
    assert "Generating new identity" in result.output
    assert "IMPORTANT: Write down your seed phrase!" in result.output
    assert "Keep this phrase secure and never share it!" in result.output

    # Verify identity was created
    assert paths.user_key_path().exists()


def test_install_without_show_seed(xdg_dirs):
    """Test install without --show-seed doesn't display mnemonic."""
    runner = CliRunner()

    result = runner.invoke(install)

    assert result.exit_code == 0
    assert "New identity created (use --show-seed to display recovery phrase)" in result.output
    assert "Write down your seed phrase!" not in result.output

    # Verify identity was created
    assert paths.user_key_path().exists()


def test_install_with_existing_identity(xdg_dirs):
    """Test install with existing identity doesn't regenerate."""
    # Create existing identity
    key = crypto.generate_key()
    crypto.save_key(key, paths.user_key_path())

    runner = CliRunner()
    result = runner.invoke(install)

    assert result.exit_code == 0
    assert "Using existing identity" in result.output

    # Verify key wasn't changed
    loaded_key = crypto.load_key(paths.user_key_path())
    assert loaded_key == key


def test_install_with_recover_valid_seed(xdg_dirs):
    """Test recovering identity from valid seed phrase."""
    # Generate a seed phrase to recover from
    mnemonic, original_key = crypto.generate_mnemonic_and_key()

    runner = CliRunner()

    # Simulate user input for seed phrase (with confirmation)
    result = runner.invoke(install, ["--recover"], input=f"{mnemonic}\n{mnemonic}\n")

    assert result.exit_code == 0
    assert "Identity Recovery" in result.output
    assert "Identity recovered successfully!" in result.output

    # Verify the recovered key matches
    recovered_key = crypto.load_key(paths.user_key_path())
    assert recovered_key == original_key


def test_install_with_recover_invalid_seed(xdg_dirs):
    """Test that recovery fails with invalid seed phrase."""
    runner = CliRunner()

    # Try with invalid seed phrase
    bad_mnemonic = "invalid seed phrase that is not valid"
    result = runner.invoke(install, ["--recover"], input=f"{bad_mnemonic}\n{bad_mnemonic}\n")

    assert result.exit_code == 1
    assert "Invalid seed phrase" in result.output

    # Verify no key was created
    assert not paths.user_key_path().exists()


def test_install_with_recover_wrong_word_count(xdg_dirs):
    """Test that recovery fails with wrong number of words."""
    runner = CliRunner()

    # Try with 12 words instead of 24
    short_mnemonic = " ".join(["abandon"] * 12)
    result = runner.invoke(install, ["--recover"], input=f"{short_mnemonic}\n{short_mnemonic}\n")

    assert result.exit_code == 1
    assert "Invalid seed phrase" in result.output


def test_export_seed_command(xdg_dirs):
    """Test export-seed command exports correct mnemonic."""
    # Create an identity
    mnemonic, key = crypto.generate_mnemonic_and_key()
    crypto.save_key(key, paths.user_key_path())

    runner = CliRunner()

    # Confirm export
    result = runner.invoke(export_seed, input="y\n")

    assert result.exit_code == 0
    assert "Your seed phrase (24 words):" in result.output
    assert mnemonic in result.output
    assert "Keep this phrase secure" in result.output


def test_export_seed_no_identity(xdg_dirs):
    """Test export-seed fails when no identity exists."""
    runner = CliRunner()

    result = runner.invoke(export_seed)

    assert result.exit_code == 1
    assert "No identity found" in result.output


def test_export_seed_cancelled(xdg_dirs):
    """Test export-seed can be cancelled."""
    # Create an identity
    key = crypto.generate_key()
    crypto.save_key(key, paths.user_key_path())

    runner = CliRunner()

    # Cancel export
    result = runner.invoke(export_seed, input="n\n")

    assert result.exit_code == 0
    assert "Your seed phrase" not in result.output


def test_install_show_seed_cancelled(xdg_dirs):
    """Test install with --show-seed can be cancelled."""
    runner = CliRunner()

    # Cancel at confirmation prompt
    result = runner.invoke(install, ["--show-seed"], input="n\n")

    # Click's confirm with abort=True returns exit code 1
    assert result.exit_code == 1
    assert "Aborted" in result.output


def test_recover_then_export_same_seed(xdg_dirs):
    """Test that recovering then exporting gives the same seed phrase."""
    # Generate original seed
    original_mnemonic, _ = crypto.generate_mnemonic_and_key()

    runner = CliRunner()

    # Recover from seed
    result = runner.invoke(install, ["--recover"], input=f"{original_mnemonic}\n{original_mnemonic}\n")
    assert result.exit_code == 0

    # Export seed
    result = runner.invoke(export_seed, input="y\n")
    assert result.exit_code == 0
    assert original_mnemonic in result.output
