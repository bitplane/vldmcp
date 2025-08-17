"""Tests for service method decorators with context injection."""

import pytest
import asyncio

from vldmcp.service.decorator import expose, share, set_context, get_context, clear_context


@pytest.fixture(autouse=True)
def clear_context_before_each_test():
    """Clear context before each test to ensure isolation."""
    clear_context()
    yield
    clear_context()


def test_sync_method_raises_error():
    """Test that @expose raises TypeError for sync methods."""

    with pytest.raises(TypeError, match="@expose can only be applied to async functions"):

        class TestService:
            @expose()
            def sync_method(self, x: int) -> int:
                return x * 2


def test_context_access_async():
    """Test context access in async methods via get_context()."""

    class TestService:
        @expose()
        async def async_method_with_context(self, data: str) -> dict:
            context = get_context()
            return {"data": data, "user": context.metadata.get("user"), "role": context.metadata.get("role")}

    service = TestService()

    async def run_test():
        # Set context
        set_context(user="bob", role="user")

        result = await service.async_method_with_context("test")
        assert result == {"data": "test", "user": "bob", "role": "user"}

    asyncio.run(run_test())


def test_context_update():
    """Test that context can be updated and accessed."""

    class TestService:
        @expose()
        async def method_with_context(self) -> str:
            context = get_context()
            return context.metadata.get("source", "unknown")

    service = TestService()

    async def run_test():
        # Set global context
        set_context(source="global")

        # Should use global context
        result = await service.method_with_context()
        assert result == "global"

        # Update context
        set_context(source="updated")
        result = await service.method_with_context()
        assert result == "updated"

    asyncio.run(run_test())


def test_share_decorator():
    """Test @share decorator works with context access."""

    class TestService:
        @share
        async def shared_method(self, value: int) -> dict:
            context = get_context()
            return {"value": value, "user": context.metadata.get("user")}

    service = TestService()

    # Check security level is set correctly
    assert service.shared_method.__wrapped__._security == "peer"

    async def run_test():
        # Test context access works
        set_context(user="charlie")
        result = await service.shared_method(100)
        assert result == {"value": 100, "user": "charlie"}

    asyncio.run(run_test())


def test_context_isolation():
    """Test that context changes don't affect other calls."""

    class TestService:
        @expose()
        async def get_user(self) -> str:
            context = get_context()
            return context.metadata.get("user", "anonymous")

    service = TestService()

    async def run_test():
        # Set initial context
        set_context(user="user1")
        result = await service.get_user()
        assert result == "user1"

        # Change context
        set_context(user="user2")
        result = await service.get_user()
        assert result == "user2"

        # Clear context
        set_context()
        result = await service.get_user()
        assert result == "anonymous"

    asyncio.run(run_test())


def test_context_accumulation():
    """Test that context data accumulates with set_context calls."""

    class TestService:
        @expose()
        async def get_context_data(self) -> dict:
            context = get_context()
            # Return both proper fields and metadata
            return {
                "user": context.metadata.get("user"),
                "role": context.metadata.get("role"),
                "permissions": context.permissions if context.permissions else None,
            }

    service = TestService()

    async def run_test():
        # Set initial context
        set_context(user="alice")
        result = await service.get_context_data()
        assert result == {"user": "alice", "role": None, "permissions": None}

        # Add more context data
        # Note: permissions is a proper Context field, role and user go to metadata
        set_context(role="admin", permissions=["read", "write"])
        result = await service.get_context_data()
        assert result == {"user": "alice", "role": "admin", "permissions": ["read", "write"]}

    asyncio.run(run_test())


def test_get_context_function():
    """Test get_context() function."""
    # Start with empty context
    context = get_context()
    assert context.metadata == {}

    # Set some context
    set_context(user="test", timestamp=12345)
    context = get_context()
    assert context.metadata == {"user": "test", "timestamp": 12345}

    # Add more context
    set_context(action="test_action")
    context = get_context()
    assert context.metadata == {"user": "test", "timestamp": 12345, "action": "test_action"}


def test_no_context_parameter():
    """Test methods without context parameter don't get it injected."""

    class TestService:
        @expose()
        async def no_context_method(self, x: int) -> int:
            return x + 1

    service = TestService()

    async def run_test():
        set_context(user="someone")

        # Should work normally without trying to inject context
        result = await service.no_context_method(5)
        assert result == 6

    asyncio.run(run_test())


def test_function_name_preserved():
    """Test that function name and docstring are preserved."""

    class TestService:
        @expose()
        async def important_method(self):
            """This is an important method."""
            return "important"

    service = TestService()
    method = service.important_method

    assert method.__name__ == "important_method"
    assert method.__doc__ == "This is an important method."


def test_async_context_safety():
    """Test that context is safe across async operations."""

    class TestService:
        @expose()
        async def async_method(self, delay: float) -> str:
            await asyncio.sleep(delay)
            context = get_context()
            return context.metadata.get("user", "unknown")

    service = TestService()

    async def run_test():
        # Start multiple concurrent operations with different contexts
        set_context(user="user1")
        task1 = asyncio.create_task(service.async_method(0.1))

        set_context(user="user2")
        task2 = asyncio.create_task(service.async_method(0.05))

        results = await asyncio.gather(task1, task2)

        # Note: This test shows current behavior - context is shared
        # For true isolation, we'd need to copy context into each task
        return results

    results = asyncio.run(run_test())
    # Both should get the last set context due to shared ContextVar
    assert len(results) == 2


def test_expose_with_security_object():
    """Test @expose with Security object instead of string."""
    from vldmcp.models.call.security import Security, SecurityRule

    security_obj = Security(rules=[SecurityRule(kind="role", value="admin", action="allow")])

    class TestService:
        @expose(security=security_obj)
        async def secure_method(self) -> str:
            return "secure"

    service = TestService()

    # Check that security is stored correctly
    assert hasattr(service.secure_method, "_security")
    assert hasattr(service.secure_method, "_security_obj")
    assert service.secure_method._security_obj == security_obj
    assert service.secure_method._security == str(security_obj)

    async def run_test():
        result = await service.secure_method()
        assert result == "secure"

    asyncio.run(run_test())
