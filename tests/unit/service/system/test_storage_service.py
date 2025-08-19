"""Tests for Storage service."""

import pytest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from vldmcp.service.system.storage import Storage


@pytest.fixture
def temp_storage():
    """Create a Storage service with temporary directories."""
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Mock the Paths to use our temporary directory
        with patch("vldmcp.service.system.storage.Paths") as mock_paths:
            mock_paths.CONFIG = temp_path / "config"
            mock_paths.DATA = temp_path / "data"
            mock_paths.STATE = temp_path / "state"
            mock_paths.CACHE = temp_path / "cache"
            mock_paths.RUNTIME = temp_path / "runtime"
            mock_paths.KEYS = temp_path / "keys"
            mock_paths.INSTALL = temp_path / "install"
            mock_paths.REPOS = temp_path / "repos"
            mock_paths.BUILD = temp_path / "build"
            mock_paths.WWW = temp_path / "www"

            storage = Storage()
            storage._temp_path = temp_path  # Store for test access
            yield storage

            # Clean up any database connections
            storage.stop()


def test_storage_initialization(temp_storage):
    """Test storage service initialization."""
    assert temp_storage.name == "storage"
    assert not temp_storage._running


def test_start_creates_directories(temp_storage):
    """Test that starting storage creates all required directories."""
    temp_storage.start()

    assert temp_storage._running

    # Check that directories were created
    base_path = temp_storage._temp_path
    assert (base_path / "config").exists()
    assert (base_path / "data").exists()
    assert (base_path / "state").exists()
    assert (base_path / "cache").exists()
    assert (base_path / "runtime").exists()
    assert (base_path / "keys").exists()
    assert (base_path / "install").exists()
    assert (base_path / "repos").exists()
    assert (base_path / "build").exists()
    assert (base_path / "www").exists()

    # Check www subdirectories
    assert (base_path / "www" / "models").exists()
    assert (base_path / "www" / "assets").exists()
    assert (base_path / "www" / "uploads").exists()
    assert (base_path / "www" / "generated").exists()


def test_user_key_path(temp_storage):
    """Test user key path generation."""
    path = temp_storage.user_key_path()
    assert str(path).endswith("keys/user.key")


def test_node_dir(temp_storage):
    """Test node directory path generation."""
    node_id = "test_node_123"
    path = temp_storage.node_dir(node_id)
    assert str(path).endswith(f"state/nodes/{node_id}")


def test_node_key_path(temp_storage):
    """Test node key path generation."""
    node_id = "test_node_123"
    path = temp_storage.node_key_path(node_id)
    assert str(path).endswith(f"state/nodes/{node_id}/key")


def test_pid_file_path(temp_storage):
    """Test PID file path generation."""
    path = temp_storage.pid_file_path()
    assert str(path).endswith("runtime/vldmcp.pid")


def test_database_path(temp_storage):
    """Test database path generation."""
    path = temp_storage.database_path("test_db")
    assert str(path).endswith("state/test_db.db")


def test_write_and_read_file(temp_storage):
    """Test writing and reading binary files."""
    temp_storage.start()

    test_path = temp_storage._temp_path / "test_file.bin"
    test_content = b"Hello, binary world!"

    # Write file
    temp_storage.write_file(test_path, test_content)

    # Check file exists
    assert temp_storage.exists(test_path)
    assert temp_storage.is_file(test_path)
    assert not temp_storage.is_dir(test_path)

    # Read file
    read_content = temp_storage.read_file(test_path)
    assert read_content == test_content


def test_write_and_read_text(temp_storage):
    """Test writing and reading text files."""
    temp_storage.start()

    test_path = temp_storage._temp_path / "test_file.txt"
    test_content = "Hello, text world! 🌍"

    # Write text file
    temp_storage.write_text(test_path, test_content)

    # Read text file
    read_content = temp_storage.read_text(test_path)
    assert read_content == test_content


def test_read_nonexistent_file(temp_storage):
    """Test reading a file that doesn't exist."""
    temp_storage.start()

    nonexistent_path = temp_storage._temp_path / "nonexistent.txt"

    with pytest.raises(FileNotFoundError):
        temp_storage.read_file(nonexistent_path)


def test_file_checks(temp_storage):
    """Test file existence and type checks."""
    temp_storage.start()

    # Test with nonexistent path
    nonexistent = temp_storage._temp_path / "nonexistent"
    assert not temp_storage.exists(nonexistent)
    assert not temp_storage.is_file(nonexistent)
    assert not temp_storage.is_dir(nonexistent)

    # Test with file
    file_path = temp_storage._temp_path / "test.txt"
    temp_storage.write_text(file_path, "test")
    assert temp_storage.exists(file_path)
    assert temp_storage.is_file(file_path)
    assert not temp_storage.is_dir(file_path)

    # Test with directory
    dir_path = temp_storage._temp_path / "test_dir"
    dir_path.mkdir()
    assert temp_storage.exists(dir_path)
    assert not temp_storage.is_file(dir_path)
    assert temp_storage.is_dir(dir_path)


def test_create_directories_creates_all_paths(temp_storage):
    """Test that create_directories creates all required paths."""
    # Don't start() to test create_directories independently
    temp_storage.create_directories()

    base_path = temp_storage._temp_path

    # Test all base directories
    assert (base_path / "config").exists()
    assert (base_path / "data").exists()
    assert (base_path / "state").exists()
    assert (base_path / "cache").exists()
    assert (base_path / "runtime").exists()
    assert (base_path / "keys").exists()
    assert (base_path / "install").exists()
    assert (base_path / "repos").exists()
    assert (base_path / "build").exists()
    assert (base_path / "www").exists()

    # Test www subdirectories
    assert (base_path / "www" / "models").exists()
    assert (base_path / "www" / "assets").exists()
    assert (base_path / "www" / "uploads").exists()
    assert (base_path / "www" / "generated").exists()


def test_write_creates_parent_directories(temp_storage):
    """Test that writing files creates parent directories."""
    temp_storage.start()

    nested_path = temp_storage._temp_path / "deep" / "nested" / "path" / "file.txt"
    content = "test content"

    # Parent directories don't exist yet
    assert not nested_path.parent.exists()

    # Write file should create parent directories
    temp_storage.write_text(nested_path, content)

    # Check file and directories exist
    assert nested_path.exists()
    assert nested_path.parent.exists()
    assert temp_storage.read_text(nested_path) == content


def test_storage_service_lifecycle(temp_storage):
    """Test storage service start and stop lifecycle."""
    # Initially not running
    assert not temp_storage._running

    # Start service
    temp_storage.start()
    assert temp_storage._running
    assert temp_storage.status() == "running"

    # Stop service
    temp_storage.stop()
    assert not temp_storage._running
    assert temp_storage.status() == "stopped"


def test_secure_permissions_called_on_start(temp_storage):
    """Test that secure permissions are applied on start."""
    # Mock the ensure_secure_permissions method to track calls
    original_method = temp_storage.ensure_secure_permissions
    call_count = 0

    def mock_secure_permissions():
        nonlocal call_count
        call_count += 1
        return original_method()

    temp_storage.ensure_secure_permissions = mock_secure_permissions

    # Start should call ensure_secure_permissions
    temp_storage.start()
    assert call_count == 1
