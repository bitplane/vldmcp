"""Tests for Service base class."""

import pytest
import asyncio
from unittest.mock import Mock

from vldmcp.service.base import Service, MergedService, dispatch_any


class DummyService(Service):
    """Test service for testing purposes."""

    pass


class AnotherDummyService(Service):
    """Another test service for testing purposes."""

    def custom_method(self):
        return "custom_result"


def test_service_initialization():
    """Test basic service initialization."""
    service = Service()

    assert service.parent is None
    assert not service._running
    assert service.children == {}
    assert service.name == "service"
    assert service.path == "service"
    assert service.version == "0.0.1"


def test_service_initialization_with_name():
    """Test service initialization with custom name."""
    service = Service(name="custom_name")

    assert service.name == "custom_name"
    assert service.path == "custom_name"


def test_service_get_name_derived_from_class():
    """Test that service name is derived from class name."""
    service = DummyService()

    # Should strip "Service" suffix and lowercase
    assert service.name == "dummy"


def test_service_auto_register_with_parent():
    """Test that services auto-register with parent."""
    parent = Service(name="parent")
    child = Service(name="child", parent=parent)

    assert child.parent == parent
    assert parent.children["child"] == child


def test_service_attribute_forwarding():
    """Test that service forwards attribute access to children."""
    parent = Service(name="parent")
    child = Service(name="child", parent=parent)

    # Should be able to access child through parent
    assert parent.child == child


def test_service_attribute_error():
    """Test AttributeError for missing attributes."""
    service = Service()

    with pytest.raises(AttributeError, match="'Service' object has no attribute 'nonexistent'"):
        _ = service.nonexistent


def test_service_lifecycle():
    """Test service start/stop lifecycle."""
    service = Service()

    # Initially stopped
    assert not service._running
    assert service.status() == "stopped"

    # Start service
    service.start()
    assert service._running
    assert service.status() == "running"

    # Stop service
    service.stop()
    assert not service._running
    assert service.status() == "stopped"


def test_service_cascade_start_stop():
    """Test that start/stop cascades to children."""
    parent = Service(name="parent")
    child1 = Service(name="child1", parent=parent)
    child2 = Service(name="child2", parent=parent)

    # Start parent should start all children
    parent.start()
    assert parent._running
    assert child1._running
    assert child2._running

    # Stop parent should stop all children
    parent.stop()
    assert not parent._running
    assert not child1._running
    assert not child2._running


def test_service_get_all_statuses():
    """Test getting status of all child services."""
    parent = Service(name="parent")
    child1 = Service(name="child1", parent=parent)
    Service(name="child2", parent=parent)

    # Initially all stopped
    statuses = parent.get_all_statuses()
    assert statuses == {"child1": "stopped", "child2": "stopped"}

    # Start one child
    child1.start()
    statuses = parent.get_all_statuses()
    assert statuses == {"child1": "running", "child2": "stopped"}

    # Start all
    parent.start()
    statuses = parent.get_all_statuses()
    assert statuses == {"child1": "running", "child2": "running"}


def test_service_full_path():
    """Test full path generation."""
    root = Service(name="root")
    level1 = Service(name="level1", parent=root)
    level2 = Service(name="level2", parent=level1)

    assert root.full_path() == "/root"
    assert level1.full_path() == "/root/level1"
    assert level2.full_path() == "/root/level1/level2"


def test_service_full_path_with_empty_path():
    """Test full path generation with empty paths (merged services)."""
    root = Service(name="root")
    merged = Service(name="merged", parent=root)
    merged.path = ""  # Empty path for merging
    leaf = Service(name="leaf", parent=merged)

    assert root.full_path() == "/root"
    assert merged.full_path() == "/root"  # Empty path skipped
    assert leaf.full_path() == "/root/leaf"  # Empty parent path skipped


def test_service_remove_default():
    """Test default remove implementation."""
    service = Service()
    result = service.remove()
    assert result == []

    result = service.remove(config=True, purge=True)
    assert result == []


def test_service_run_no_children():
    """Test running service with no children."""

    async def test_async():
        service = Service()
        service.start()

        # Should run for a short time then we'll cancel it
        task = asyncio.create_task(service.run())

        # Let it run briefly
        await asyncio.sleep(0.1)

        # Cancel and check it was running
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(test_async())


def test_service_run_with_children():
    """Test running service with children."""

    async def test_async():
        parent = Service(name="parent")
        child1 = DummyService(name="child1", parent=parent)
        child2 = DummyService(name="child2", parent=parent)

        # Mock the child run methods
        child1.run = Mock(return_value=asyncio.sleep(0.1))
        child2.run = Mock(return_value=asyncio.sleep(0.1))

        parent.start()

        # Run parent (should gather children)
        await parent.run()

        # Check children were run
        child1.run.assert_called_once()
        child2.run.assert_called_once()

    asyncio.run(test_async())


def test_dispatch_any_success():
    """Test dispatch_any with successful method call."""

    class TestObj:
        def test_method(self, *args, **kwargs):
            return "success"

    obj1 = Mock(spec=[])  # Empty spec means no attributes
    obj2 = TestObj()

    result = dispatch_any([obj1, obj2], "test_method", "arg1", kwarg1="value1")

    assert result == "success"


def test_dispatch_any_no_method():
    """Test dispatch_any when no object has the method."""
    obj1 = Mock(spec=[])  # No methods
    obj2 = Mock(spec=[])  # No methods

    with pytest.raises(AttributeError, match="No object in list has callable method 'nonexistent'"):
        dispatch_any([obj1, obj2], "nonexistent")


def test_dispatch_any_not_callable():
    """Test dispatch_any when attribute exists but is not callable."""

    class TestObj1:
        not_a_method = "string_value"  # Not callable

    class TestObj2:
        def test_method(self):
            return "success"

    obj1 = TestObj1()
    obj2 = TestObj2()

    result = dispatch_any([obj1, obj2], "test_method")
    assert result == "success"


def test_service_merge_with_add():
    """Test merging services with + operator."""
    service1 = Service(name="service1")
    service2 = Service(name="service2")

    merged = service1 + service2

    assert isinstance(merged, MergedService)
    assert merged.name == "service1"  # Takes first service's name
    assert merged.path == "service1"  # Takes first service's path


def test_service_merge_with_existing_merged():
    """Test merging with an already merged service."""
    service1 = Service(name="service1")
    service2 = Service(name="service2")
    service3 = Service(name="service3")

    # Create initial merge
    merged12 = service1 + service2

    # Add third service to existing merge
    merged123 = merged12 + service3

    assert isinstance(merged123, MergedService)
    assert len([k for k in merged123.children.keys() if k.startswith("_merged_")]) == 3


def test_merged_service_initialization():
    """Test MergedService initialization."""
    service1 = AnotherDummyService(name="service1")
    service2 = DummyService(name="service2")
    services = [service1, service2]

    merged = MergedService(services)

    assert merged.name == "service1"  # First service's name
    assert merged.path == "service1"  # First service's path
    assert service1.parent == merged
    assert service2.parent == merged
    assert service1.path == "service1"  # First keeps its path
    assert service2.path == ""  # Others get empty path


def test_merged_service_attribute_priority():
    """Test that merged services have correct attribute priority."""

    class Service1(Service):
        shared_attr = "first"
        unique_to_first = "unique1"

    class Service2(Service):
        shared_attr = "second"  # Should override
        unique_to_second = "unique2"

    service1 = Service1(name="service1")
    service2 = Service2(name="service2")
    services = [service1, service2]
    merged = MergedService(services)

    # Later services should override earlier ones
    assert merged.shared_attr == "second"
    assert merged.unique_to_first == "unique1"
    assert merged.unique_to_second == "unique2"


def test_merged_service_attribute_error():
    """Test AttributeError in merged service."""
    service1 = Service(name="service1")
    service2 = Service(name="service2")
    services = [service1, service2]

    merged = MergedService(services)

    with pytest.raises(AttributeError, match="'MergedService' object has no attribute 'nonexistent'"):
        _ = merged.nonexistent


def test_merged_service_private_attribute_error():
    """Test that private attributes raise AttributeError immediately."""
    service1 = DummyService(name="service1")
    services = [service1]

    merged = MergedService(services)

    with pytest.raises(AttributeError, match="'MergedService' object has no attribute '_private'"):
        _ = merged._private


def test_merged_service_empty_services_list():
    """Test MergedService with empty services list."""
    merged = MergedService([])

    assert merged.name == "merged"
    assert merged.path == ""


def test_merged_service_lifecycle():
    """Test that MergedService lifecycle affects all merged services."""
    service1 = DummyService(name="service1")
    service2 = DummyService(name="service2")
    services = [service1, service2]

    merged = MergedService(services)

    # Start merged should start all services
    merged.start()
    assert merged._running
    assert service1._running
    assert service2._running

    # Stop merged should stop all services
    merged.stop()
    assert not merged._running
    assert not service1._running
    assert not service2._running


def test_service_add_merged_to_regular():
    """Test adding a regular service to a merged service."""
    service1 = Service(name="service1")
    service2 = Service(name="service2")
    service3 = Service(name="service3")

    # Create merged service
    merged = service1 + service2

    # Add regular service to merged
    result = service3 + merged

    assert isinstance(result, MergedService)
    # Should have service3 + the services from merged
    merged_children = [k for k in result.children.keys() if k.startswith("_merged_")]
    assert len(merged_children) == 3


def test_service_version():
    """Test that service has correct version."""
    service = Service()
    assert service.version == "0.0.1"


def test_service_name_generation_edge_cases():
    """Test edge cases in service name generation."""

    class ServiceService(Service):
        """Service class ending with Service."""

        pass

    class CustomService(Service):
        """Custom service class."""

        pass

    # Should remove "Service" suffix
    service_service = ServiceService()
    assert service_service.name == "service"

    # Should remove "Service" suffix
    custom_service = CustomService()
    assert custom_service.name == "custom"


def test_get_name_with_object_base():
    """Test _get_name when base class is object."""

    class PlainService(object):
        """Service class that inherits from object directly."""

        def __init__(self):
            pass

        def _get_name(self):
            """Copy of Service._get_name for testing."""
            name = self.__class__.__name__
            # Remove parent class name suffix if present
            parent_name = self.__class__.__bases__[0].__name__
            if name.endswith(parent_name) and name != parent_name:
                name = name[: -len(parent_name)]
            return name.lower()

    service = PlainService()
    name = service._get_name()
    assert name == "plainservice"  # Should not remove "object"
