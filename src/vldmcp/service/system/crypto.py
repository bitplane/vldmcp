"""Cryptographic service for vldmcp.

Seed phrase (BIP-39) <-> 32-byte key for vldmcp.

Alignment with Veilid:
- Veilid keys are 32 bytes (Ed25519). We keep that as our on-disk identity.
- Veilid publishes no mnemonic/wordlist spec, so we use standard BIP-39 English.
- We enforce 24 words (256-bit entropy) and round-trip exactly between key and mnemonic.

This service provides:
- generate_key(): 32 random bytes
- mnemonic_from_key(key32): 24-word BIP-39 (English) from 32-byte key
- key_from_mnemonic(mnemonic): 32-byte key from 24-word mnemonic
- generate_mnemonic_and_key(): create both in one go
- ensure_user_key()/ensure_node_key(): same semantics as before

NOTE: Both `mnemonic` and `pynacl` are required dependencies.
"""

from __future__ import annotations

import secrets
from pathlib import Path

from mnemonic import Mnemonic
from nacl.signing import SigningKey
from nacl.encoding import RawEncoder
import blake3

from ..base import Service
from .storage import Storage


class CryptoService(Service):
    """Service that manages cryptographic operations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mnemonic = Mnemonic("english")

    def start(self):
        """Initialize crypto service."""
        super().start()

    def stop(self):
        """Stop crypto service."""
        super().stop()

    def generate_key(self) -> bytes:
        """Generate a new 32-byte key.

        Returns:
            32 random bytes suitable for use as a Veilid identity key
        """
        return secrets.token_bytes(32)

    def mnemonic_from_key(self, key: bytes) -> str:
        """Convert a 32-byte key to a 24-word BIP-39 mnemonic phrase.

        Args:
            key: 32-byte key

        Returns:
            24-word mnemonic phrase

        Raises:
            ValueError: If key is not exactly 32 bytes
        """
        if len(key) != 32:
            raise ValueError(f"Key must be exactly 32 bytes, got {len(key)}")

        # Convert 32 bytes to 256 bits of entropy
        entropy = key
        mnemonic = self._mnemonic.to_mnemonic(entropy)

        # Verify we get exactly 24 words
        words = mnemonic.split()
        if len(words) != 24:
            raise ValueError(f"Expected 24 words, got {len(words)}")

        return mnemonic

    def key_from_mnemonic(self, mnemonic: str) -> bytes:
        """Convert a 24-word mnemonic phrase to a 32-byte key.

        Args:
            mnemonic: 24-word BIP-39 mnemonic phrase

        Returns:
            32-byte key

        Raises:
            ValueError: If mnemonic is invalid or not 24 words
        """
        if not self.is_valid_mnemonic(mnemonic):
            raise ValueError("Invalid mnemonic phrase")

        words = mnemonic.strip().split()
        if len(words) != 24:
            raise ValueError(f"Expected 24 words, got {len(words)}")

        # Convert mnemonic to entropy (should be 32 bytes)
        entropy = self._mnemonic.to_entropy(mnemonic)

        if len(entropy) != 32:
            raise ValueError(f"Expected 32 bytes of entropy, got {len(entropy)}")

        return entropy

    def generate_mnemonic_and_key(self) -> tuple[str, bytes]:
        """Generate a new mnemonic phrase and corresponding key.

        Returns:
            Tuple of (24-word mnemonic phrase, 32-byte key)
        """
        key = self.generate_key()
        mnemonic = self.mnemonic_from_key(key)
        return mnemonic, key

    def is_valid_mnemonic(self, mnemonic: str) -> bool:
        """Check if a mnemonic phrase is valid BIP-39.

        Args:
            mnemonic: Mnemonic phrase to validate

        Returns:
            True if valid, False otherwise
        """
        return self._mnemonic.check(mnemonic)

    def save_key(self, key: bytes, path: Path) -> None:
        """Save a key to a file with secure permissions.

        Args:
            key: Key bytes to save (must be exactly 32 bytes)
            path: Path to save the key file

        Raises:
            ValueError: If key is not exactly 32 bytes
        """
        if len(key) != 32:
            raise ValueError(f"Key must be exactly 32 bytes, got {len(key)}")

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write key with secure permissions
        path.write_bytes(key)
        path.chmod(0o600)  # Owner read/write only

    def load_key(self, path: Path) -> bytes | None:
        """Load a key from a file.

        Args:
            path: Path to load the key from

        Returns:
            32-byte key if file exists and is valid, None otherwise
        """
        if not path.exists():
            return None

        try:
            key = path.read_bytes()
            if len(key) != 32:
                return None
            return key
        except OSError:
            return None

    def ensure_user_key(self, storage_service: Storage | None = None) -> bytes:
        """Ensure the user identity key exists (32 bytes), generating if necessary.

        Args:
            storage_service: Storage service to get key path from

        Returns:
            The user identity key

        Raises:
            ValueError: If no storage service provided
        """
        if storage_service is None:
            # Try to get storage from parent
            if self.parent:
                storage_service = self.parent.storage
            else:
                raise ValueError("Storage service is required")

        user_key_path = storage_service.user_key_path()

        # Load existing key if it exists
        existing_key = self.load_key(user_key_path)
        if existing_key:
            return existing_key

        # Generate new key
        key = self.generate_key()
        self.save_key(key, user_key_path)
        return key

    def ensure_node_key(self, node_id: str, storage_service: Storage | None = None) -> bytes:
        """Ensure a node key exists (32 bytes), generating if necessary.

        Args:
            node_id: Node identifier
            storage_service: Storage service to get key path from

        Returns:
            The node key

        Raises:
            ValueError: If no storage service provided
        """
        if storage_service is None:
            # Try to get storage from parent
            if self.parent:
                storage_service = self.parent.storage
            else:
                raise ValueError("Storage service is required")

        node_key_path = storage_service.node_key_path(node_id)

        # Load existing key if it exists
        existing_key = self.load_key(node_key_path)
        if existing_key:
            return existing_key

        # Generate new key
        key = self.generate_key()
        self.save_key(key, node_key_path)
        return key

    def generate_node_id(self, key: bytes) -> str:
        """Generate a node ID from a key.

        Args:
            key: 32-byte private key

        Returns:
            40-character hex string node ID (derived from public key hash)
        """
        if len(key) != 32:
            raise ValueError(f"Key must be exactly 32 bytes, got {len(key)}")

        # Derive public key from private key
        signing_key = SigningKey(key)
        public_key = signing_key.verify_key.encode()

        # Hash the public key to get node ID
        return blake3.blake3(public_key).hexdigest()[:40]


def ed25519_keypair_from_seed(seed32: bytes) -> tuple[bytes, bytes]:
    """Return (public_key32, private_key64) from a 32-byte Ed25519 seed.

    Not needed for storage; useful for signing/tests.
    """
    if len(seed32) != 32:
        raise ValueError("Seed must be 32 bytes for Ed25519.")
    sk = SigningKey(seed32)
    pk = sk.verify_key
    return (pk.encode(encoder=RawEncoder), sk.encode(encoder=RawEncoder))


def generate_node_id() -> str:
    """Generate a random node ID (hex)."""
    return secrets.token_hex(16)
