"""Pretty printing utilities for vldmcp."""

import base32hex
import hashlib
import base58


def pprint_size(size_bytes: int) -> str:
    """Convert bytes to human-readable size string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string (e.g., "1.2G", "456M", "789K")
    """
    if size_bytes == 0:
        return "0B"

    units = ["B", "K", "M", "G", "T", "P"]
    size = float(size_bytes)
    for unit in units[:-1]:
        if size < 1024.0:
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}{units[-1]}"


def pprint_dict(
    obj: dict | list, prefix: str = "", output_func=None, tab_separated: bool = False, filter_empty: bool = False
) -> None:
    """Pretty print a dictionary or list with dot notation for nested keys.

    Args:
        obj: Dictionary or list to pretty print
        prefix: Current key prefix for nested objects
        output_func: Function to use for output (default: print, can be click.echo)
        tab_separated: Use tab-separated format instead of colon format
        filter_empty: Skip empty/zero values
    """
    if output_func is None:
        output_func = print

    result = _format_dict(obj, prefix, tab_separated=tab_separated, filter_empty=filter_empty)
    for line in result:
        output_func(line)


def _format_dict(
    obj: dict | list, prefix: str = "", tab_separated: bool = False, filter_empty: bool = False
) -> list[str]:
    """Format a dictionary or list for pretty printing.

    Args:
        obj: Object to format
        prefix: Current key prefix for nested objects
        tab_separated: Use tab-separated format instead of colon format
        filter_empty: Skip empty/zero values

    Returns:
        List of formatted strings
    """
    result = []
    separator = "\t" if tab_separated else ": "

    if isinstance(obj, dict):
        for key, value in obj.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                result.extend(_format_dict(value, new_prefix, tab_separated=tab_separated, filter_empty=filter_empty))
            elif isinstance(value, list):
                # Format lists inline
                formatted_value = _format_value(value)
                if not filter_empty or (value and value != 0 and value != "0B"):
                    result.append(f"{new_prefix}{separator}{formatted_value}")
            else:
                formatted_value = _format_value(value)
                if not filter_empty or (value and value != 0 and value != "0B"):
                    result.append(f"{new_prefix}{separator}{formatted_value}")
    elif isinstance(obj, list):
        for item in obj:
            result.extend(_format_dict(item, prefix, tab_separated=tab_separated, filter_empty=filter_empty))
    else:
        if prefix:
            formatted_value = _format_value(obj)
            if not filter_empty or (obj and obj != 0 and obj != "0B"):
                result.append(f"{prefix}{separator}{formatted_value}")

    return result


def _format_value(value) -> str:
    """Format a value for pretty printing.

    Args:
        value: Value to format

    Returns:
        Formatted string
    """
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    elif isinstance(value, int) and value > 255:
        return str(value)
    else:
        return str(value)


def pprint_pubkey(pubkey: bytes, format: str = "short") -> str:
    """Format an Ed25519 public key for display.

    Args:
        pubkey: 32-byte Ed25519 public key
        format: Display format - "short", "veilid", "onion", or "full"

    Returns:
        Formatted public key string

    Raises:
        ValueError: If pubkey is not exactly 32 bytes
    """
    if len(pubkey) != 32:
        raise ValueError(f"Public key must be exactly 32 bytes, got {len(pubkey)}")

    if format == "short":
        # Show first 8 chars of hex
        return pubkey.hex()[:8] + "..."
    elif format == "veilid":
        # Veilid format: VLD0:<base58>
        return f"VLD0:{base58.b58encode(pubkey).decode()}"
    elif format == "onion":
        # Tor v3 onion address
        return pubkey_to_onion(pubkey)
    elif format == "full":
        # Full hex
        return pubkey.hex()
    else:
        raise ValueError(f"Unknown format: {format}")


def pubkey_to_onion(pubkey: bytes) -> str:
    """Convert Ed25519 public key to Tor v3 onion address.

    Args:
        pubkey: 32-byte Ed25519 public key

    Returns:
        Tor v3 onion address (e.g., "abc123...def.onion")
    """
    if len(pubkey) != 32:
        raise ValueError(f"Public key must be exactly 32 bytes, got {len(pubkey)}")

    # Tor v3 onion address calculation
    checksum_input = b".onion checksum" + pubkey + b"\x03"
    checksum = hashlib.sha3_256(checksum_input).digest()[:2]

    # Encode: pubkey + checksum + version (0x03)
    address_bytes = pubkey + checksum + b"\x03"
    address = base32hex.b32encode(address_bytes).lower().rstrip("=")

    return f"{address}.onion"


def pubkey_to_veilid(pubkey: bytes) -> str:
    """Convert Ed25519 public key to Veilid identity string.

    Args:
        pubkey: 32-byte Ed25519 public key

    Returns:
        Veilid identity string (e.g., "VLD0:...")
    """
    if len(pubkey) != 32:
        raise ValueError(f"Public key must be exactly 32 bytes, got {len(pubkey)}")

    return f"VLD0:{base58.b58encode(pubkey).decode()}"
