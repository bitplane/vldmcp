"""Seed phrase (BIP-39) <-> 32-byte key for vldmcp.

Alignment with Veilid:
- Veilid keys are 32 bytes (Ed25519). We keep that as our on-disk identity.
- Veilid publishes no mnemonic/wordlist spec, so we use standard BIP-39 English.
- We enforce 24 words (256-bit entropy) and round-trip exactly between key and mnemonic.

This module provides:
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
from typing import Optional, Tuple

from mnemonic import Mnemonic
from nacl.signing import SigningKey
from nacl.encoding import RawEncoder

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .file_service import FileService


# -------------------------------
# Raw 32-byte key (seed) handling
# -------------------------------


def generate_key() -> bytes:
    """Generate a new 32-byte cryptographic seed (Ed25519-compatible)."""
    return secrets.token_bytes(32)


def save_key(key: bytes, key_path: Path) -> None:
    """Save a key to a file with secure permissions."""
    if len(key) != 32:
        raise ValueError("Key must be exactly 32 bytes.")
    key_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    key_path.write_bytes(key)
    key_path.chmod(0o600)


def load_key(key_path: Path) -> Optional[bytes]:
    """Load a key from a file if it exists."""
    if not key_path.exists():
        return None
    data = key_path.read_bytes()
    if len(data) != 32:
        raise ValueError(f"Key file {key_path} is {len(data)} bytes; expected 32.")
    return data


def ensure_user_key(file_service: Optional["FileService"] = None) -> bytes:
    """Ensure the user identity key exists (32 bytes), generating if necessary."""
    if file_service:
        user_key_path = file_service.user_key_path()
    else:
        raise ValueError("FileService is required")

    key = load_key(user_key_path)
    if key is not None:
        return key
    key = generate_key()
    save_key(key, user_key_path)
    return key


def ensure_node_key(node_id: str, file_service: Optional["FileService"] = None) -> bytes:
    """Ensure a node key exists (32 bytes), generating if necessary."""
    if file_service:
        node_key_path = file_service.node_key_path(node_id)
    else:
        raise ValueError("FileService is required")

    key = load_key(node_key_path)
    if key is not None:
        return key
    key = generate_key()
    save_key(key, node_key_path)
    return key


def generate_node_id() -> str:
    """Generate a random node ID (hex)."""
    return secrets.token_hex(16)


# ---------------------------------
# BIP-39 mnemonic <-> 32-byte key
# ---------------------------------

_MN = Mnemonic("english")


def is_valid_mnemonic(mnemonic: str) -> bool:
    """True if the string is a valid BIP-39 English mnemonic (checksum/wordlist)."""
    return _MN.check(mnemonic)


def mnemonic_from_key(key32: bytes) -> str:
    """Export a 24-word BIP-39 mnemonic from a 32-byte key.

    Treats key bytes as 256-bit entropy (+ checksum) for exact round-trip.
    """
    if len(key32) != 32:
        raise ValueError("Key must be exactly 32 bytes to export as a 24-word mnemonic.")
    return _MN.to_mnemonic(key32)


def key_from_mnemonic(mnemonic: str) -> bytes:
    """Import a 32-byte key from a 24-word BIP-39 mnemonic (English).

    Exact inverse of mnemonic_from_key().
    """
    if not _MN.check(mnemonic):
        raise ValueError("Invalid BIP-39 mnemonic (wordlist/checksum).")
    entropy = _MN.to_entropy(mnemonic)
    if len(entropy) != 32:
        raise ValueError(f"Expected 32 bytes entropy from mnemonic, got {len(entropy)}.")
    # Ensure we return bytes, not bytearray
    return bytes(entropy)


def generate_mnemonic_and_key() -> Tuple[str, bytes]:
    """Generate a new 24-word mnemonic and its 32-byte key."""
    mnemonic = _MN.generate(strength=256)  # 24 words
    key = key_from_mnemonic(mnemonic)  # exact inverse path
    return mnemonic, key


# -------------------------------
# Optional: Ed25519 convenience
# -------------------------------


def ed25519_keypair_from_seed(seed32: bytes) -> Tuple[bytes, bytes]:
    """Return (public_key32, private_key64) from a 32-byte Ed25519 seed.

    Not needed for storage; useful for signing/tests.
    """
    if len(seed32) != 32:
        raise ValueError("Seed must be 32 bytes for Ed25519.")
    sk = SigningKey(seed32)
    pk = sk.verify_key
    return (pk.encode(encoder=RawEncoder), sk.encode(encoder=RawEncoder))
