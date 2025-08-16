"""Seed phrase (BIP-39) <-> 32-byte key for vldmcp.

Alignment with Veilid:
- Veilid keys are 32 bytes (Ed25519). We keep that as our on-disk identity.
- Veilid publishes no mnemonic/wordlist spec, so we use standard BIP-39 English.
- We enforce 24 words (256-bit entropy) and round-trip exactly between key and mnemonic.

This module provides backward compatibility by importing from the service.
All new code should use the CryptoService directly.

NOTE: Both `mnemonic` and `pynacl` are required dependencies.
"""

from __future__ import annotations


from .service.system.crypto import (
    CryptoService,
    generate_key,
    mnemonic_from_key,
    key_from_mnemonic,
    generate_mnemonic_and_key,
    is_valid_mnemonic,
    save_key,
    load_key,
    ensure_user_key,
    ensure_node_key,
)

# Re-export Ed25519 functionality
from nacl.signing import SigningKey
from nacl.encoding import RawEncoder


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
    import secrets

    return secrets.token_hex(16)


# Backward compatibility exports
__all__ = [
    "CryptoService",
    "generate_key",
    "mnemonic_from_key",
    "key_from_mnemonic",
    "generate_mnemonic_and_key",
    "is_valid_mnemonic",
    "save_key",
    "load_key",
    "ensure_user_key",
    "ensure_node_key",
    "generate_node_id",
    "ed25519_keypair_from_seed",
]
