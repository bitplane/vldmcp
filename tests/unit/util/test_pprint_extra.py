"""Additional tests for pprint utilities."""

import pytest
import hashlib

from vldmcp.util.pprint import (
    pprint_size,
    pprint_dict,
    _format_dict,
    _format_value,
    pprint_pubkey,
    pubkey_to_onion,
    pubkey_to_veilid,
)


def test_pprint_size_zero():
    """Test size formatting for zero bytes."""
    assert pprint_size(0) == "0B"


def test_pprint_size_bytes():
    """Test size formatting for bytes."""
    assert pprint_size(1) == "1.0B"
    assert pprint_size(512) == "512.0B"
    assert pprint_size(1023) == "1023.0B"


def test_pprint_size_kilobytes():
    """Test size formatting for kilobytes."""
    assert pprint_size(1024) == "1.0K"
    assert pprint_size(1536) == "1.5K"
    assert pprint_size(1024 * 1023) == "1023.0K"


def test_pprint_size_megabytes():
    """Test size formatting for megabytes."""
    assert pprint_size(1024 * 1024) == "1.0M"
    assert pprint_size(1024 * 1024 * 1.5) == "1.5M"
    assert pprint_size(1024 * 1024 * 1023) == "1023.0M"


def test_pprint_size_gigabytes():
    """Test size formatting for gigabytes."""
    assert pprint_size(1024 * 1024 * 1024) == "1.0G"
    assert pprint_size(int(1024 * 1024 * 1024 * 2.5)) == "2.5G"


def test_pprint_size_terabytes():
    """Test size formatting for terabytes."""
    assert pprint_size(1024 * 1024 * 1024 * 1024) == "1.0T"
    assert pprint_size(int(1024 * 1024 * 1024 * 1024 * 1.7)) == "1.7T"


def test_pprint_size_petabytes():
    """Test size formatting for petabytes."""
    assert pprint_size(1024 * 1024 * 1024 * 1024 * 1024) == "1.0P"


def test_pprint_dict_simple():
    """Test printing simple dictionary."""
    data = {"key1": "value1", "key2": 42}

    # Capture printed output
    import io
    import sys

    captured_output = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured_output

    try:
        pprint_dict(data)
        output = captured_output.getvalue()
    finally:
        sys.stdout = old_stdout

    lines = output.strip().split("\n")
    assert len(lines) == 2
    assert "key1: value1" in lines
    assert "key2: 42" in lines


def test_pprint_dict_nested():
    """Test printing nested dictionary."""
    data = {"level1": {"level2": {"value": "nested"}, "simple": "value"}}

    result = _format_dict(data)

    assert "level1.level2.value: nested" in result
    assert "level1.simple: value" in result


def test_pprint_dict_with_lists():
    """Test printing dictionary with lists."""
    data = {"simple_list": [1, 2, 3], "mixed_list": ["a", 42, True], "nested": {"inner_list": ["x", "y", "z"]}}

    result = _format_dict(data)

    # Check list formatting
    assert "simple_list: 1, 2, 3" in result
    assert "mixed_list: a, 42, True" in result
    assert "nested.inner_list: x, y, z" in result


def test_pprint_dict_empty():
    """Test printing empty dictionary."""
    result = _format_dict({})
    assert result == []


def test_pprint_dict_with_prefix():
    """Test printing with prefix."""
    data = {"key": "value"}
    result = _format_dict(data, prefix="prefix")

    assert result == ["prefix.key: value"]


def test_format_value_list():
    """Test formatting list values."""
    assert _format_value([1, 2, 3]) == "1, 2, 3"
    assert _format_value(["a", "b", "c"]) == "a, b, c"
    assert _format_value([]) == ""


def test_format_value_large_int():
    """Test formatting large integer values."""
    assert _format_value(256) == "256"
    assert _format_value(1000) == "1000"
    assert _format_value(255) == "255"  # Boundary case


def test_format_value_other_types():
    """Test formatting other value types."""
    assert _format_value("string") == "string"
    assert _format_value(42) == "42"
    assert _format_value(True) == "True"
    assert _format_value(None) == "None"


def test_pprint_pubkey_valid_32_bytes():
    """Test public key formatting with valid 32-byte key."""
    pubkey = b"\x01" * 32  # 32 bytes of 0x01

    # Test short format
    short = pprint_pubkey(pubkey, "short")
    assert short == "01010101..."

    # Test full format
    full = pprint_pubkey(pubkey, "full")
    assert full == "01" * 32


def test_pprint_pubkey_invalid_length():
    """Test public key formatting with invalid length."""
    invalid_key = b"\x01" * 31  # 31 bytes

    with pytest.raises(ValueError, match="Public key must be exactly 32 bytes, got 31"):
        pprint_pubkey(invalid_key, "short")


def test_pprint_pubkey_veilid_format():
    """Test Veilid format public key."""
    pubkey = b"\x01" * 32

    veilid = pprint_pubkey(pubkey, "veilid")
    assert veilid.startswith("VLD0:")

    # Should be same as direct function
    direct = pubkey_to_veilid(pubkey)
    assert veilid == direct


def test_pprint_pubkey_onion_format():
    """Test onion format public key."""
    pubkey = b"\x01" * 32

    onion = pprint_pubkey(pubkey, "onion")
    assert onion.endswith(".onion")

    # Should be same as direct function
    direct = pubkey_to_onion(pubkey)
    assert onion == direct


def test_pprint_pubkey_unknown_format():
    """Test unknown format raises error."""
    pubkey = b"\x01" * 32

    with pytest.raises(ValueError, match="Unknown format: invalid"):
        pprint_pubkey(pubkey, "invalid")


def test_pubkey_to_onion_valid():
    """Test converting public key to onion address."""
    pubkey = b"\x01" * 32

    onion = pubkey_to_onion(pubkey)

    # Should be valid onion format
    assert onion.endswith(".onion")
    assert len(onion) > 16  # Onion addresses are long

    # Verify it's reproducible
    onion2 = pubkey_to_onion(pubkey)
    assert onion == onion2


def test_pubkey_to_onion_invalid_length():
    """Test onion conversion with invalid key length."""
    invalid_key = b"\x01" * 30

    with pytest.raises(ValueError, match="Public key must be exactly 32 bytes, got 30"):
        pubkey_to_onion(invalid_key)


def test_pubkey_to_onion_algorithm():
    """Test onion address generation algorithm."""
    pubkey = b"\x00" * 32  # Use known input

    # Manually calculate expected result
    checksum_input = b".onion checksum" + pubkey + b"\x03"
    checksum = hashlib.sha3_256(checksum_input).digest()[:2]
    address_bytes = pubkey + checksum + b"\x03"

    import base32hex

    expected = base32hex.b32encode(address_bytes).lower().rstrip("=") + ".onion"

    result = pubkey_to_onion(pubkey)
    assert result == expected


def test_pubkey_to_veilid_valid():
    """Test converting public key to Veilid identity."""
    pubkey = b"\x01" * 32

    veilid = pubkey_to_veilid(pubkey)

    # Should start with VLD0:
    assert veilid.startswith("VLD0:")

    # Should be reproducible
    veilid2 = pubkey_to_veilid(pubkey)
    assert veilid == veilid2


def test_pubkey_to_veilid_invalid_length():
    """Test Veilid conversion with invalid key length."""
    invalid_key = b"\x01" * 33

    with pytest.raises(ValueError, match="Public key must be exactly 32 bytes, got 33"):
        pubkey_to_veilid(invalid_key)


def test_pubkey_to_veilid_algorithm():
    """Test Veilid identity generation uses base58."""
    pubkey = b"\x00" * 32  # Use known input

    import base58

    expected = f"VLD0:{base58.b58encode(pubkey).decode()}"

    result = pubkey_to_veilid(pubkey)
    assert result == expected


def test_format_dict_with_list_input():
    """Test _format_dict with list input."""
    data = [{"name": "item1", "value": 100}, {"name": "item2", "value": 200}]

    result = _format_dict(data)

    # Should format each item in the list
    assert len(result) == 4  # 2 items × 2 fields each
    assert "name: item1" in result
    assert "value: 100" in result
    assert "name: item2" in result
    assert "value: 200" in result


def test_format_dict_with_non_dict_list():
    """Test _format_dict with non-dict objects."""
    data = "simple_string"

    result = _format_dict(data, prefix="test")
    assert result == ["test: simple_string"]


def test_format_dict_empty_prefix():
    """Test _format_dict with empty prefix."""
    data = {"key": "value"}
    result = _format_dict(data, prefix="")

    assert result == ["key: value"]


def test_pprint_dict_real_example():
    """Test with realistic data structure."""
    data = {
        "server": {"host": "localhost", "port": 8080, "ssl": True},
        "database": {"url": "sqlite:///app.db", "pool_size": 10},
        "features": ["auth", "cache", "logging"],
        "version": "1.0.0",
    }

    result = _format_dict(data)

    expected_lines = [
        "server.host: localhost",
        "server.port: 8080",
        "server.ssl: True",
        "database.url: sqlite:///app.db",
        "database.pool_size: 10",
        "features: auth, cache, logging",
        "version: 1.0.0",
    ]

    for expected in expected_lines:
        assert expected in result


def test_edge_case_very_large_size():
    """Test size formatting with very large numbers."""
    # Test beyond petabytes
    huge_size = 1024**6  # Exabyte
    result = pprint_size(huge_size)
    assert result.endswith("P")  # Should still use petabytes as max unit


def test_edge_case_pubkey_different_bytes():
    """Test public key formatting with different byte patterns."""
    # Test with all different values
    pubkey = bytes(range(32))  # 0x00, 0x01, 0x02, ..., 0x1f

    short = pprint_pubkey(pubkey, "short")
    assert short == "00010203..."

    full = pprint_pubkey(pubkey, "full")
    assert len(full) == 64  # 32 bytes = 64 hex chars
    assert full.startswith("000102")
    assert full.endswith("1e1f")
