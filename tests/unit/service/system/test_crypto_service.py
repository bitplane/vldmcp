"""Tests for CryptoService class methods."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from vldmcp.service.system.crypto import CryptoService


@pytest.fixture
def crypto_service():
    """Create a CryptoService instance."""
    return CryptoService()


def test_crypto_service_name():
    """Test crypto service name."""
    assert CryptoService.name() == "crypto"


def test_generate_key_length(crypto_service):
    """Test that generate_key returns exactly 32 bytes."""
    key = crypto_service.generate_key()
    assert len(key) == 32
    assert isinstance(key, bytes)


def test_generate_key_randomness(crypto_service):
    """Test that generate_key produces different keys."""
    key1 = crypto_service.generate_key()
    key2 = crypto_service.generate_key()
    assert key1 != key2


def test_mnemonic_from_key_valid(crypto_service):
    """Test converting valid 32-byte key to mnemonic."""
    key = b"a" * 32  # 32 bytes of 'a'
    mnemonic = crypto_service.mnemonic_from_key(key)

    assert isinstance(mnemonic, str)
    words = mnemonic.split()
    assert len(words) == 24


def test_mnemonic_from_key_invalid_length(crypto_service):
    """Test that invalid key length raises ValueError."""
    with pytest.raises(ValueError, match="Key must be exactly 32 bytes, got 31"):
        crypto_service.mnemonic_from_key(b"a" * 31)

    with pytest.raises(ValueError, match="Key must be exactly 32 bytes, got 33"):
        crypto_service.mnemonic_from_key(b"a" * 33)


def test_key_from_mnemonic_invalid_word_count(crypto_service):
    """Test that invalid word count raises ValueError."""
    with pytest.raises(ValueError, match="Invalid mnemonic phrase"):
        crypto_service.key_from_mnemonic("word " * 12)


def test_key_from_mnemonic_invalid_checksum(crypto_service):
    """Test that invalid mnemonic raises ValueError."""
    # 24 invalid words
    invalid_mnemonic = "invalid " * 24
    with pytest.raises(ValueError, match="Invalid mnemonic phrase"):
        crypto_service.key_from_mnemonic(invalid_mnemonic)


def test_is_valid_mnemonic_false(crypto_service):
    """Test is_valid_mnemonic with invalid input."""
    assert not crypto_service.is_valid_mnemonic("invalid words here")
    assert not crypto_service.is_valid_mnemonic("")
    assert not crypto_service.is_valid_mnemonic("word " * 12)  # Wrong count


def test_round_trip_key_mnemonic(crypto_service):
    """Test that key -> mnemonic -> key is consistent."""
    original_key = crypto_service.generate_key()
    mnemonic = crypto_service.mnemonic_from_key(original_key)
    recovered_key = crypto_service.key_from_mnemonic(mnemonic)

    assert original_key == recovered_key


def test_generate_mnemonic_and_key(crypto_service):
    """Test generate_mnemonic_and_key returns consistent pair."""
    mnemonic, key = crypto_service.generate_mnemonic_and_key()

    assert len(key) == 32
    assert len(mnemonic.split()) == 24

    # Verify consistency
    recovered_key = crypto_service.key_from_mnemonic(mnemonic)
    assert key == recovered_key


def test_save_and_load_key(crypto_service):
    """Test saving and loading keys from files."""
    with TemporaryDirectory() as tmp_dir:
        key_path = Path(tmp_dir) / "test.key"
        original_key = crypto_service.generate_key()

        # Save key
        crypto_service.save_key(original_key, key_path)

        # Verify file exists and has correct permissions
        assert key_path.exists()
        assert key_path.stat().st_mode & 0o777 == 0o600

        # Load key
        loaded_key = crypto_service.load_key(key_path)
        assert loaded_key == original_key


def test_save_key_invalid_length(crypto_service):
    """Test that saving invalid key length raises ValueError."""
    with TemporaryDirectory() as tmp_dir:
        key_path = Path(tmp_dir) / "test.key"

        with pytest.raises(ValueError, match="Key must be exactly 32 bytes, got 31"):
            crypto_service.save_key(b"a" * 31, key_path)


def test_load_key_nonexistent(crypto_service):
    """Test loading from nonexistent file returns None."""
    result = crypto_service.load_key(Path("/nonexistent/path"))
    assert result is None


def test_load_key_invalid_size(crypto_service):
    """Test loading invalid size key returns None."""
    with TemporaryDirectory() as tmp_dir:
        key_path = Path(tmp_dir) / "invalid.key"
        key_path.write_bytes(b"wrong_size")

        result = crypto_service.load_key(key_path)
        assert result is None


def test_generate_node_id(crypto_service):
    """Test generate_node_id creates secure hash from public key."""
    key = b"a" * 32
    node_id = crypto_service.generate_node_id(key)

    assert isinstance(node_id, str)
    assert len(node_id) == 40  # blake3 hash truncated to 40 chars
    # Should be deterministic for same key
    assert node_id == crypto_service.generate_node_id(key)
    # Should not be the raw key
    assert node_id != key.hex()


def test_generate_node_id_invalid_length(crypto_service):
    """Test generate_node_id with invalid key length."""
    with pytest.raises(ValueError, match="Key must be exactly 32 bytes, got 31"):
        crypto_service.generate_node_id(b"a" * 31)


def test_service_lifecycle(crypto_service):
    """Test service start/stop lifecycle."""
    assert not crypto_service._running

    crypto_service.start()
    assert crypto_service._running

    crypto_service.stop()
    assert not crypto_service._running
