"""Tests for BIP-39 seed phrase functionality in crypto module."""

import pytest
from vldmcp import crypto


def test_generate_key():
    """Test that generate_key creates 32-byte keys."""
    key1 = crypto.generate_key()
    key2 = crypto.generate_key()

    assert isinstance(key1, bytes)
    assert len(key1) == 32
    assert isinstance(key2, bytes)
    assert len(key2) == 32
    assert key1 != key2  # Should be random


def test_save_and_load_key(tmp_path):
    """Test saving and loading keys from files."""
    key_path = tmp_path / "test.key"
    original_key = crypto.generate_key()

    # Save key
    crypto.save_key(original_key, key_path)

    # Check file permissions
    assert key_path.exists()
    assert oct(key_path.stat().st_mode)[-3:] == "600"

    # Load key
    loaded_key = crypto.load_key(key_path)
    assert loaded_key == original_key

    # Test loading non-existent file
    missing_path = tmp_path / "missing.key"
    assert crypto.load_key(missing_path) is None


def test_save_key_invalid_size(tmp_path):
    """Test that save_key rejects invalid key sizes."""
    key_path = tmp_path / "test.key"

    with pytest.raises(ValueError, match="Key must be exactly 32 bytes"):
        crypto.save_key(b"too short", key_path)

    with pytest.raises(ValueError, match="Key must be exactly 32 bytes"):
        crypto.save_key(b"x" * 33, key_path)


def test_load_key_invalid_size(tmp_path):
    """Test that load_key rejects files with wrong size."""
    key_path = tmp_path / "bad.key"
    key_path.write_bytes(b"wrong size")

    with pytest.raises(ValueError, match="expected 32"):
        crypto.load_key(key_path)


def test_generate_mnemonic_and_key():
    """Test generating a new mnemonic and key pair."""
    mnemonic, key = crypto.generate_mnemonic_and_key()

    # Check mnemonic format
    assert isinstance(mnemonic, str)
    words = mnemonic.split()
    assert len(words) == 24  # BIP-39 24-word phrase

    # Check key
    assert isinstance(key, bytes)
    assert len(key) == 32

    # Verify mnemonic is valid
    assert crypto.is_valid_mnemonic(mnemonic)


def test_mnemonic_key_round_trip():
    """Test that key -> mnemonic -> key round-trips correctly."""
    # Generate original key
    original_key = crypto.generate_key()

    # Convert to mnemonic
    mnemonic = crypto.mnemonic_from_key(original_key)
    assert isinstance(mnemonic, str)
    assert len(mnemonic.split()) == 24

    # Convert back to key
    recovered_key = crypto.key_from_mnemonic(mnemonic)
    assert recovered_key == original_key


def test_key_from_mnemonic_invalid():
    """Test that key_from_mnemonic rejects invalid mnemonics."""
    # Invalid checksum
    bad_mnemonic = "abandon " * 24  # Not a valid checksum
    with pytest.raises(ValueError, match="Invalid BIP-39 mnemonic"):
        crypto.key_from_mnemonic(bad_mnemonic)

    # Invalid word
    bad_mnemonic = "notaword " + " ".join(["abandon"] * 23)
    with pytest.raises(ValueError, match="Invalid BIP-39 mnemonic"):
        crypto.key_from_mnemonic(bad_mnemonic)


def test_mnemonic_from_key_invalid_size():
    """Test that mnemonic_from_key rejects wrong-sized keys."""
    with pytest.raises(ValueError, match="Key must be exactly 32 bytes"):
        crypto.mnemonic_from_key(b"too short")

    with pytest.raises(ValueError, match="Key must be exactly 32 bytes"):
        crypto.mnemonic_from_key(b"x" * 31)


def test_is_valid_mnemonic():
    """Test mnemonic validation."""
    # Generate a valid mnemonic
    mnemonic, _ = crypto.generate_mnemonic_and_key()
    assert crypto.is_valid_mnemonic(mnemonic) is True

    # Test invalid cases
    assert crypto.is_valid_mnemonic("not a valid mnemonic") is False
    assert crypto.is_valid_mnemonic("abandon " * 24) is False  # Bad checksum
    assert crypto.is_valid_mnemonic("") is False


def test_consistent_mnemonic_generation():
    """Test that the same key always produces the same mnemonic."""
    key = crypto.generate_key()

    mnemonic1 = crypto.mnemonic_from_key(key)
    mnemonic2 = crypto.mnemonic_from_key(key)

    assert mnemonic1 == mnemonic2


def test_different_keys_different_mnemonics():
    """Test that different keys produce different mnemonics."""
    key1 = crypto.generate_key()
    key2 = crypto.generate_key()

    mnemonic1 = crypto.mnemonic_from_key(key1)
    mnemonic2 = crypto.mnemonic_from_key(key2)

    assert mnemonic1 != mnemonic2


def test_real_bip39_test_vector():
    """Test with a known BIP-39 test vector to ensure compatibility."""
    # This is a known test vector - 32 bytes of 0x00
    test_key = b"\x00" * 32
    expected_words_start = "abandon abandon abandon"  # First 3 words for all-zero entropy

    mnemonic = crypto.mnemonic_from_key(test_key)
    assert mnemonic.startswith(expected_words_start)

    # Round-trip should work
    recovered = crypto.key_from_mnemonic(mnemonic)
    assert recovered == test_key


def test_ed25519_keypair_generation():
    """Test Ed25519 keypair generation."""
    seed = crypto.generate_key()
    public_key, private_key = crypto.ed25519_keypair_from_seed(seed)

    assert isinstance(public_key, bytes)
    assert len(public_key) == 32
    assert isinstance(private_key, bytes)
    assert len(private_key) == 32  # Ed25519 seed/private key


def test_ed25519_invalid_seed_size():
    """Test that ed25519_keypair_from_seed rejects wrong-sized seeds."""
    with pytest.raises(ValueError, match="Seed must be 32 bytes"):
        crypto.ed25519_keypair_from_seed(b"too short")


def test_generate_node_id():
    """Test node ID generation."""
    id1 = crypto.generate_node_id()
    id2 = crypto.generate_node_id()

    assert isinstance(id1, str)
    assert isinstance(id2, str)
    assert len(id1) == 32  # 16 bytes as hex
    assert len(id2) == 32
    assert id1 != id2  # Should be random


def test_integration_full_identity_lifecycle(file_service):
    """Test the full identity lifecycle: create, export, recover."""

    # 1. Generate new identity
    mnemonic1, key1 = crypto.generate_mnemonic_and_key()
    user_key_path = file_service.user_key_path()
    crypto.save_key(key1, user_key_path)

    # 2. Export seed phrase
    loaded_key = crypto.load_key(user_key_path)
    exported_mnemonic = crypto.mnemonic_from_key(loaded_key)
    assert exported_mnemonic == mnemonic1

    # 3. Delete identity
    user_key_path.unlink()
    assert not user_key_path.exists()

    # 4. Recover from seed phrase
    recovered_key = crypto.key_from_mnemonic(exported_mnemonic)
    crypto.save_key(recovered_key, user_key_path)

    # 5. Verify recovery worked
    final_key = crypto.load_key(user_key_path)
    assert final_key == key1
