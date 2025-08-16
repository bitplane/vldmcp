"""Tests for service name derivation."""

from vldmcp.service import Service


def test_service_name_base_class():
    """Test that base Service class returns lowercase name."""
    service = Service()
    assert service.name == "service"


def test_service_name_removes_parent_suffix():
    """Test that child classes remove parent class name suffix."""

    class FooService(Service):
        pass

    service = FooService()
    assert service.name == "foo"


def test_service_name_inheritance_chain():
    """Test service name derivation through inheritance chain."""

    class FooService(Service):
        pass

    class BarFooService(FooService):
        pass

    foo_service = FooService()
    bar_service = BarFooService()
    assert foo_service.name == "foo"
    assert bar_service.name == "bar"  # Removes "FooService"


def test_service_name_no_suffix_removal():
    """Test that names not ending with parent name are just lowercased."""

    class CustomThing(Service):
        pass

    service = CustomThing()
    assert service.name == "customthing"


def test_service_name_case_handling():
    """Test that names are properly lowercased."""

    class HTTPService(Service):
        pass

    service = HTTPService()
    assert service.name == "http"


def test_service_name_real_codebase_examples():
    """Test with actual classes from the codebase."""
    from vldmcp.service.system.crypto import CryptoService
    from vldmcp.service.system.storage import Storage
    from vldmcp.service.platform.native import NativePlatform

    crypto = CryptoService()
    storage = Storage()
    platform = NativePlatform()

    assert crypto.name == "crypto"
    assert storage.name == "storage"
    assert platform.name == "native"  # NativePlatform inherits from Platform
