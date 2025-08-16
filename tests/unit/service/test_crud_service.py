"""Tests for CRUD service operations."""

import pytest
from datetime import datetime, timedelta, UTC
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Optional

from sqlmodel import SQLModel, Field

from vldmcp.service.crud import CRUDService
from vldmcp.service.system.storage import Storage


class CrudTestModel(SQLModel, table=True):
    """Test model for CRUD operations."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="Name field")
    value: int = Field(description="Value field")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Creation time")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Update time")


@pytest.fixture
def temp_storage():
    """Create temporary storage for testing."""
    with TemporaryDirectory() as temp_dir:
        storage = Storage()
        storage._data_home = Path(temp_dir)
        yield storage


@pytest.fixture
def crud_service(temp_storage):
    """Create a CRUD service with test model."""
    service = CRUDService(temp_storage, models=[CrudTestModel])
    # Clear any existing data for clean tests
    service.delete("crudtestmodel")
    return service


def test_create_record(crud_service):
    """Test creating a new record."""
    record = crud_service.create("crudtestmodel", name="test1", value=100)

    assert record.id is not None
    assert record.name == "test1"
    assert record.value == 100
    assert record.created_at is not None
    assert record.updated_at is not None


def test_read_records(crud_service):
    """Test reading records with filters."""
    # Create test data
    crud_service.create("crudtestmodel", name="test1", value=100)
    crud_service.create("crudtestmodel", name="test2", value=200)
    crud_service.create("crudtestmodel", name="test1", value=150)

    # Read all records
    all_records = crud_service.read("crudtestmodel")
    assert len(all_records) == 3

    # Read with name filter
    name_filtered = crud_service.read("crudtestmodel", name="test1")
    assert len(name_filtered) == 2

    # Read with value filter
    value_filtered = crud_service.read("crudtestmodel", value=200)
    assert len(value_filtered) == 1
    assert value_filtered[0].name == "test2"


def test_update_records(crud_service):
    """Test updating records."""
    # Create test data
    crud_service.create("crudtestmodel", name="test1", value=100)
    crud_service.create("crudtestmodel", name="test2", value=200)

    # Update by name
    count = crud_service.update("crudtestmodel", {"name": "test1"}, {"value": 999})
    assert count == 1

    # Verify update
    updated = crud_service.read("crudtestmodel", name="test1")
    assert len(updated) == 1
    assert updated[0].value == 999
    assert updated[0].updated_at > updated[0].created_at

    # Other record should be unchanged
    unchanged = crud_service.read("crudtestmodel", name="test2")
    assert unchanged[0].value == 200


def test_delete_records(crud_service):
    """Test deleting records."""
    # Create test data
    crud_service.create("crudtestmodel", name="test1", value=100)
    crud_service.create("crudtestmodel", name="test2", value=200)
    crud_service.create("crudtestmodel", name="test1", value=150)

    # Delete by name
    count = crud_service.delete("crudtestmodel", name="test1")
    assert count == 2

    # Verify deletion
    remaining = crud_service.read("crudtestmodel")
    assert len(remaining) == 1
    assert remaining[0].name == "test2"


def test_upsert_create(crud_service):
    """Test upsert creating new record."""
    record = crud_service.upsert("crudtestmodel", ["name"], name="test1", value=100)

    assert record.id is not None
    assert record.name == "test1"
    assert record.value == 100


def test_upsert_update(crud_service):
    """Test upsert updating existing record."""
    # Create initial record
    original = crud_service.create("crudtestmodel", name="test1", value=100)
    original_id = original.id
    original_created = original.created_at

    # Upsert should update
    updated = crud_service.upsert("crudtestmodel", ["name"], name="test1", value=999)

    assert updated.id == original_id  # Same record
    assert updated.value == 999  # Updated value
    assert updated.created_at == original_created  # Created time unchanged
    assert updated.updated_at > original.updated_at  # Updated time changed


def test_get_records_since(crud_service):
    """Test getting records since timestamp."""
    # Create a record
    past_time = datetime.now(UTC) - timedelta(hours=1)
    record = crud_service.create("crudtestmodel", name="test1", value=100)

    # Should find record
    recent = crud_service.get_records_since("crudtestmodel", past_time)
    assert len(recent) >= 1
    assert record.id in [r.id for r in recent]

    # Should not find from future
    future_time = datetime.now(UTC) + timedelta(hours=1)
    future_records = crud_service.get_records_since("crudtestmodel", future_time)
    assert len(future_records) == 0


def test_model_attribute_access(crud_service):
    """Test that models are accessible as attributes."""
    assert hasattr(crud_service, "crudtestmodel")
    assert crud_service.crudtestmodel == CrudTestModel


def test_invalid_model_name(crud_service):
    """Test error handling for invalid model names."""
    with pytest.raises(ValueError, match="Unknown model: nonexistent"):
        crud_service.create("nonexistent", name="test")

    with pytest.raises(ValueError, match="Unknown model: nonexistent"):
        crud_service.read("nonexistent")

    with pytest.raises(ValueError, match="Unknown model: nonexistent"):
        crud_service.update("nonexistent", {}, {})

    with pytest.raises(ValueError, match="Unknown model: nonexistent"):
        crud_service.delete("nonexistent")

    with pytest.raises(ValueError, match="Unknown model: nonexistent"):
        crud_service.upsert("nonexistent", [])


def test_get_records_since_no_updated_at():
    """Test error when model doesn't have updated_at field."""

    class NoTimestampModel(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str = Field()

    with TemporaryDirectory() as temp_dir:
        storage = Storage()
        storage._data_home = Path(temp_dir)
        crud_service = CRUDService(storage, models=[NoTimestampModel])

        with pytest.raises(ValueError, match="does not have updated_at field"):
            crud_service.get_records_since("notimestampmodel", datetime.now(UTC))
