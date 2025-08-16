"""Key management service for vldmcp."""

from pathlib import Path
from .service import Service
from . import crypto


class KeyService(Service):
    """Service that manages cryptographic keys."""

    @classmethod
    def name(cls) -> str:
        return "keys"

    def start(self):
        """Ensure keys exist on start."""
        self.ensure_user_key()
        self._running = True

    def stop(self):
        """Nothing to do on stop."""
        self._running = False

    def ensure_user_key(self) -> bytes:
        """Ensure the user identity key exists, generating if necessary.

        Returns:
            The user key bytes
        """
        return crypto.ensure_user_key(self.parent.files)

    def ensure_node_key(self, node_id: str) -> bytes:
        """Ensure a node key exists, generating if necessary.

        Args:
            node_id: Node identifier

        Returns:
            The node key bytes
        """
        return crypto.ensure_node_key(node_id, self.parent.files)

    def generate_key(self) -> bytes:
        """Generate a new 32-byte key.

        Returns:
            New key bytes
        """
        return crypto.generate_key()

    def generate_mnemonic_and_key(self) -> tuple[str, bytes]:
        """Generate a new mnemonic phrase and corresponding key.

        Returns:
            Tuple of (mnemonic phrase, key bytes)
        """
        return crypto.generate_mnemonic_and_key()

    def key_from_mnemonic(self, mnemonic: str) -> bytes:
        """Derive a key from a mnemonic phrase.

        Args:
            mnemonic: BIP39 mnemonic phrase

        Returns:
            Derived key bytes
        """
        return crypto.key_from_mnemonic(mnemonic)

    def mnemonic_from_key(self, key: bytes) -> str:
        """Convert a key to a mnemonic phrase.

        Args:
            key: 32-byte key

        Returns:
            BIP39 mnemonic phrase
        """
        return crypto.mnemonic_from_key(key)

    def is_valid_mnemonic(self, mnemonic: str) -> bool:
        """Check if a mnemonic phrase is valid.

        Args:
            mnemonic: Mnemonic phrase to validate

        Returns:
            True if valid, False otherwise
        """
        return crypto.is_valid_mnemonic(mnemonic)

    def save_key(self, key: bytes, path: Path) -> None:
        """Save a key to a file with secure permissions.

        Args:
            key: Key bytes to save
            path: Path to save to
        """
        crypto.save_key(key, path)

    def load_key(self, path: Path) -> bytes | None:
        """Load a key from a file.

        Args:
            path: Path to load from

        Returns:
            Key bytes if found, None otherwise
        """
        return crypto.load_key(path)
