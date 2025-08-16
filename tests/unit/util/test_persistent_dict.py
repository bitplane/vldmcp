"""Tests for PersistentDict utility."""

import pytest
import uuid
from tempfile import TemporaryDirectory
from pathlib import Path

from vldmcp.util.persistent_dict import PersistentDict
from vldmcp.service.system.storage import Storage


@pytest.fixture
def temp_storage():
    """Create temporary storage for testing."""
    with TemporaryDirectory() as temp_dir:
        storage = Storage()
        storage._data_home = Path(temp_dir)
        yield storage


@pytest.fixture
def persistent_dict(temp_storage):
    """Create a PersistentDict with temporary storage."""
    # Use unique filename per test to avoid sharing state
    filename = f"test_config_{uuid.uuid4().hex[:8]}.toml"
    return PersistentDict(temp_storage, filename)


def test_empty_dict_creation(persistent_dict):
    """Test creating empty persistent dict."""
    assert len(persistent_dict) == 0
    assert list(persistent_dict.keys()) == []
    assert list(persistent_dict.values()) == []
    assert list(persistent_dict.items()) == []


def test_set_and_get_items(persistent_dict):
    """Test setting and getting items."""
    persistent_dict["key1"] = "value1"
    persistent_dict["key2"] = 42
    persistent_dict["key3"] = {"nested": "dict"}

    assert persistent_dict["key1"] == "value1"
    assert persistent_dict["key2"] == 42
    assert persistent_dict["key3"] == {"nested": "dict"}

    assert len(persistent_dict) == 3


def test_contains_and_get(persistent_dict):
    """Test contains and get methods."""
    persistent_dict["exists"] = "value"

    assert "exists" in persistent_dict
    assert "missing" not in persistent_dict

    assert persistent_dict.get("exists") == "value"
    assert persistent_dict.get("missing") is None
    assert persistent_dict.get("missing", "default") == "default"


def test_delete_items(persistent_dict):
    """Test deleting items."""
    persistent_dict["key1"] = "value1"
    persistent_dict["key2"] = "value2"

    assert len(persistent_dict) == 2

    del persistent_dict["key1"]

    assert len(persistent_dict) == 1
    assert "key1" not in persistent_dict
    assert "key2" in persistent_dict


def test_iteration(persistent_dict):
    """Test iterating over dict."""
    persistent_dict["a"] = 1
    persistent_dict["b"] = 2
    persistent_dict["c"] = 3

    keys = list(persistent_dict.keys())
    values = list(persistent_dict.values())
    items = list(persistent_dict.items())

    assert set(keys) == {"a", "b", "c"}
    assert set(values) == {1, 2, 3}
    assert set(items) == {("a", 1), ("b", 2), ("c", 3)}

    # Test __iter__
    iter_keys = list(persistent_dict)
    assert set(iter_keys) == {"a", "b", "c"}


def test_clear(persistent_dict):
    """Test clearing the dict."""
    persistent_dict["key1"] = "value1"
    persistent_dict["key2"] = "value2"

    assert len(persistent_dict) == 2

    persistent_dict.clear()

    assert len(persistent_dict) == 0
    assert list(persistent_dict.keys()) == []


def test_persistence_across_instances(temp_storage):
    """Test that data persists across different instances."""
    # Create first instance and add data
    dict1 = PersistentDict(temp_storage, "persist_test.toml")
    dict1["persistent_key"] = "persistent_value"
    dict1["number"] = 123

    # Create second instance and verify data exists
    dict2 = PersistentDict(temp_storage, "persist_test.toml")
    assert dict2["persistent_key"] == "persistent_value"
    assert dict2["number"] == 123
    assert len(dict2) == 2


def test_lazy_loading(temp_storage):
    """Test that data is only loaded when accessed."""
    # Create first instance and add data
    dict1 = PersistentDict(temp_storage, "lazy_test.toml")
    dict1["test"] = "value"

    # Create second instance but don't access data
    dict2 = PersistentDict(temp_storage, "lazy_test.toml")
    assert not dict2._loaded  # Should not be loaded yet

    # Access data should trigger loading
    _ = dict2["test"]
    assert dict2._loaded  # Now should be loaded


def test_auto_save_on_modification(temp_storage):
    """Test that modifications auto-save to disk."""
    from vldmcp.util.paths import Paths

    dict1 = PersistentDict(temp_storage, "autosave_test.toml")
    config_path = Paths.CONFIG / "autosave_test.toml"

    # Remove file if it exists from previous tests
    if config_path.exists():
        config_path.unlink()

    # Initially no file
    assert not config_path.exists()

    # Set value should create file
    dict1["key"] = "value"
    assert config_path.exists()

    # Verify file contents
    dict2 = PersistentDict(temp_storage, "autosave_test.toml")
    assert dict2["key"] == "value"

    # Delete should update file
    del dict1["key"]
    dict3 = PersistentDict(temp_storage, "autosave_test.toml")
    assert len(dict3) == 0


def test_missing_key_error(persistent_dict):
    """Test that missing keys raise KeyError."""
    with pytest.raises(KeyError):
        _ = persistent_dict["nonexistent"]


def test_delete_missing_key_error(persistent_dict):
    """Test that deleting missing keys raises KeyError."""
    with pytest.raises(KeyError):
        del persistent_dict["nonexistent"]


def test_complex_data_types(persistent_dict):
    """Test storing complex data types that TOML supports."""
    data = {
        "string": "text",
        "integer": 42,
        "float": 3.14,
        "boolean": True,
        "array": [1, 2, 3],
        "nested": {"inner": "value", "number": 123},
    }

    for key, value in data.items():
        persistent_dict[key] = value

    for key, value in data.items():
        assert persistent_dict[key] == value


def test_file_path_directory_creation(temp_storage):
    """Test that nested directory paths are created."""
    from vldmcp.util.paths import Paths

    nested_dict = PersistentDict(temp_storage, "nested/deep/config.toml")
    nested_dict["test"] = "value"

    config_path = Paths.CONFIG / "nested/deep/config.toml"
    assert config_path.exists()
    assert config_path.parent.exists()


def test_load_existing_file(temp_storage):
    """Test loading from existing TOML file."""
    import tomli_w
    from vldmcp.util.paths import Paths

    # Create TOML file manually
    config_path = Paths.CONFIG / "existing.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = {"preexisting": "data", "number": 456}
    with open(config_path, "wb") as f:
        tomli_w.dump(data, f)

    # Load with PersistentDict
    persistent_dict = PersistentDict(temp_storage, "existing.toml")
    assert persistent_dict["preexisting"] == "data"
    assert persistent_dict["number"] == 456
    assert len(persistent_dict) == 2


def test_manual_load_and_save(persistent_dict):
    """Test manual load and save operations."""
    # Add data and manually save
    persistent_dict.data = {"manual": "data"}
    persistent_dict.save()

    # Create new instance and manually load
    new_dict = PersistentDict(persistent_dict.storage, persistent_dict.file_path)
    new_dict.load()

    assert new_dict.data == {"manual": "data"}
    assert new_dict["manual"] == "data"
