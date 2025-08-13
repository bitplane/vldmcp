"""Cryptographic key management for vldmcp.

This module handles generation and management of user identity keys and node keys.
"""

import secrets
from pathlib import Path
from typing import Optional

from . import paths


def generate_key() -> bytes:
    """Generate a new cryptographic key.

    Returns a 32-byte random key suitable for cryptographic operations.
    """
    return secrets.token_bytes(32)


def save_key(key: bytes, key_path: Path) -> None:
    """Save a key to a file with secure permissions.

    Args:
        key: The key bytes to save
        key_path: Path where to save the key
    """
    # Ensure parent directory exists with secure permissions
    key_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    # Write key to file
    key_path.write_bytes(key)

    # Set secure file permissions
    key_path.chmod(0o600)


def load_key(key_path: Path) -> Optional[bytes]:
    """Load a key from a file.

    Args:
        key_path: Path to the key file

    Returns:
        The key bytes if the file exists, None otherwise
    """
    if not key_path.exists():
        return None
    return key_path.read_bytes()


def ensure_user_key() -> bytes:
    """Ensure the user identity key exists, generating if necessary.

    Returns:
        The user identity key bytes
    """
    user_key_path = paths.user_key_path()

    # Try to load existing key
    key = load_key(user_key_path)
    if key is not None:
        return key

    # Generate new key
    key = generate_key()
    save_key(key, user_key_path)

    return key


def ensure_node_key(node_id: str) -> bytes:
    """Ensure a node key exists, generating if necessary.

    Args:
        node_id: The node identifier

    Returns:
        The node key bytes
    """
    node_key_path = paths.node_key_path(node_id)

    # Try to load existing key
    key = load_key(node_key_path)
    if key is not None:
        return key

    # Generate new key
    key = generate_key()
    save_key(key, node_key_path)

    return key


def generate_node_id() -> str:
    """Generate a new random node ID.

    Returns:
        A hex-encoded random node ID
    """
    return secrets.token_hex(16)
