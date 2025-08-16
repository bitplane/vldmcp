"""Service method exposure decorators with context injection."""

import functools
import inspect
from typing import Callable
from contextvars import ContextVar
from contextlib import asynccontextmanager

# Context variables for request context
request_context: ContextVar[dict] = ContextVar("request_context", default={})


def expose(security: str = "owner"):
    """Expose an async service method with automatic context injection.

    Args:
        security: Security level - "owner" (default) or "peers"
    """

    def decorator(func: Callable) -> Callable:
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f"@expose can only be applied to async functions, got {func.__name__}")

        func._security = security

        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # Always inject context - it's invisible to the method signature
            kwargs["context"] = request_context.get({})
            return await func(self, *args, **kwargs)

        return async_wrapper

    return decorator


def set_context(**context_data):
    """Set the current request context."""
    if not context_data:
        # Clear context when called with no arguments
        request_context.set({})
    else:
        # Create new dict instead of mutating existing one
        current = request_context.get({}).copy()
        current.update(context_data)
        request_context.set(current)


def clear_context():
    """Clear the current request context."""
    request_context.set({})


def get_context() -> dict:
    """Get the current request context."""
    return request_context.get({})


# @share is just @expose with security="peers"
def share(func: Callable) -> Callable:
    """Share a service method with peers (equivalent to @expose(security="peers"))."""
    return expose(security="peers")(func)


@asynccontextmanager
async def context_scope(**context_data):
    """Async context manager for setting request context with automatic cleanup."""
    # Get current context and create new one with updates
    current = request_context.get({}).copy()
    current.update(context_data)

    # Set the new context
    token = request_context.set(current)
    try:
        yield current
    finally:
        # Reset to previous context
        request_context.reset(token)
