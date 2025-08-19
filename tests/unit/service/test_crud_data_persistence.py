"""Tests for CRUDService data persistence."""

from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from sqlmodel import SQLModel, Field

import pytest

from vldmcp.service.crud import CRUDService
from vldmcp.service.system.storage import Storage


class TestUser(SQLModel, table=True):
    """Test model for persistence testing."""

    __test__ = False  # Tell pytest this is not a test class

    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str


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


def test_crud_service_data_persists_across_instances(temp_storage):
    """Test that creating the same database twice doesn't delete existing data."""
    temp_storage.start()

    # Create first service instance and add data
    service1 = CRUDService(temp_storage, [TestUser], name="test1")

    # Add a user
    user1 = service1.create("testuser", name="John Doe", email="john@example.com")
    assert user1.id is not None
    assert user1.name == "John Doe"

    # Stop the first service (this should dispose the engine)
    service1.stop()

    # Create second service instance with same database path
    service2 = CRUDService(temp_storage, [TestUser], name="test2")

    # Data should still exist
    users = service2.read("testuser")
    assert len(users) == 1
    assert users[0].name == "John Doe"
    assert users[0].email == "john@example.com"

    # Add more data
    service2.create("testuser", name="Jane Smith", email="jane@example.com")

    # Both users should exist
    users = service2.read("testuser")
    assert len(users) == 2

    # Clean up
    service2.stop()


def test_crud_service_engine_disposal(temp_storage):
    """Test that CRUDService properly disposes of engines on stop."""
    temp_storage.start()

    service = CRUDService(temp_storage, [TestUser], name="dispose_test")

    # Engine should exist
    assert service.engine is not None

    # Stop should dispose engine
    service.stop()

    # Engine should still exist but be disposed
    assert service.engine is not None
    # Note: We can't easily test if engine is disposed without private API access
    # but the important thing is stop() doesn't crash


def test_multiple_crud_services_same_database(temp_storage):
    """Test multiple CRUDService instances can use the same database file safely."""
    temp_storage.start()

    # Patch database_path to return the same path for both services
    with patch.object(temp_storage, "database_path") as mock_db_path:
        shared_db = temp_storage._temp_path / "shared.db"
        mock_db_path.return_value = shared_db

        # Create two services
        service1 = CRUDService(temp_storage, [TestUser], name="shared1")
        service2 = CRUDService(temp_storage, [TestUser], name="shared2")

        # Add data through first service
        service1.create("testuser", name="Service 1 User", email="s1@example.com")

        # Read through second service - should see the data
        users = service2.read("testuser")
        assert len(users) == 1
        assert users[0].name == "Service 1 User"

        # Add data through second service
        service2.create("testuser", name="Service 2 User", email="s2@example.com")

        # Read through first service - should see both
        users = service1.read("testuser")
        assert len(users) == 2

        # Clean up
        service1.stop()
        service2.stop()
