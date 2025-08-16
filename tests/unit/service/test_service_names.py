"""Tests for service name derivation."""

from vldmcp.service import Service


def test_service_name_base_class():
    """Test that base Service class returns lowercase name."""
    assert Service.name() == "service"


def test_service_name_removes_parent_suffix():
    """Test that child classes remove parent class name suffix."""

    class FooService(Service):
        pass

    assert FooService.name() == "foo"


def test_service_name_inheritance_chain():
    """Test service name derivation through inheritance chain."""

    class FooService(Service):
        pass

    class BarFooService(FooService):
        pass

    assert FooService.name() == "foo"
    assert BarFooService.name() == "bar"  # Removes "FooService"


def test_service_name_no_suffix_removal():
    """Test that names not ending with parent name are just lowercased."""

    class CustomThing(Service):
        pass

    assert CustomThing.name() == "customthing"


def test_service_name_case_handling():
    """Test that names are properly lowercased."""

    class HTTPService(Service):
        pass

    assert HTTPService.name() == "http"


def test_service_name_real_codebase_examples():
    """Test with actual classes from the codebase."""
    from vldmcp.service.system.crypto import CryptoService
    from vldmcp.service.system.storage import Storage
    from vldmcp.service.platform.native import NativePlatform

    assert CryptoService.name() == "crypto"
    assert Storage.name() == "storage"
    assert NativePlatform.name() == "native"  # NativePlatform inherits from Platform
