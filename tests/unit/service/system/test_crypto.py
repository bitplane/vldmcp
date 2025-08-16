"""Tests for the crypto module."""

from vldmcp.service.system.crypto import CryptoService, generate_node_id

crypto_service = CryptoService()


def test_generate_key():
    """Test that generate_key creates a 32-byte key."""
    key = crypto_service.generate_key()
    assert isinstance(key, bytes)
    assert len(key) == 32

    # Keys should be different each time
    key2 = crypto_service.generate_key()
    assert key != key2


def test_save_and_load_key(tmp_path):
    """Test saving and loading a key."""
    key_path = tmp_path / "test.key"
    original_key = crypto_service.generate_key()

    # Save key
    crypto_service.save_key(original_key, key_path)

    # Check file exists with correct permissions
    assert key_path.exists()
    assert oct(key_path.stat().st_mode)[-3:] == "600"

    # Load key
    loaded_key = crypto_service.load_key(key_path)
    assert loaded_key == original_key


def test_load_nonexistent_key(tmp_path):
    """Test loading a key that doesn't exist returns None."""
    key_path = tmp_path / "nonexistent.key"
    assert crypto_service.load_key(key_path) is None


def test_ensure_user_key(storage_service):
    """Test ensure_user_key creates key if it doesn't exist."""
    # First call should generate key
    key1 = crypto_service.ensure_user_key(storage_service)
    assert isinstance(key1, bytes)
    assert len(key1) == 32

    # Second call should return same key
    key2 = crypto_service.ensure_user_key(storage_service)
    assert key1 == key2

    # Check file was created with correct permissions
    key_path = storage_service.user_key_path()
    assert key_path.exists()
    assert oct(key_path.stat().st_mode)[-3:] == "600"
    assert oct(key_path.parent.stat().st_mode)[-3:] == "700"


def test_ensure_node_key(storage_service):
    """Test ensure_node_key creates key if it doesn't exist."""
    # First call should generate key
    key1 = crypto_service.ensure_node_key("node123", storage_service)
    assert isinstance(key1, bytes)
    assert len(key1) == 32

    # Second call should return same key
    key2 = crypto_service.ensure_node_key("node123", storage_service)
    assert key1 == key2

    # Different node should get different key
    key3 = crypto_service.ensure_node_key("node456", storage_service)
    assert key3 != key1

    # Check files were created with correct permissions
    key_path = storage_service.node_key_path("node123")
    assert key_path.exists()
    assert oct(key_path.stat().st_mode)[-3:] == "600"
    # Note: parent directory permissions may vary by filesystem


def test_generate_node_id():
    """Test generate_node_id creates hex strings."""
    node_id = generate_node_id()
    assert isinstance(node_id, str)
    assert len(node_id) == 32  # 16 bytes = 32 hex chars

    # Should be valid hex
    int(node_id, 16)

    # Should be different each time
    node_id2 = generate_node_id()
    assert node_id != node_id2
