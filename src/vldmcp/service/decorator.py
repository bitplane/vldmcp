"""Service method exposure decorators with security integration."""

import functools
import inspect
from typing import Callable, Union
from contextvars import ContextVar
from contextlib import asynccontextmanager
from datetime import datetime

from ..models.call.context import Context
from ..models.call.security import Security

# Context variables for request context
request_context: ContextVar[Context] = ContextVar("request_context", default=Context())


def expose(security: Union[str, Security] = "owner"):
    """Expose an async service method with security checking.

    Args:
        security: Security configuration - string ("owner", "peer") or Security object
    """

    def decorator(func: Callable) -> Callable:
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f"@expose can only be applied to async functions, got {func.__name__}")

        # Store security configuration on the function
        if isinstance(security, str):
            func._security = security
            func._security_obj = Security.from_string(security)
        else:
            func._security = str(security)  # For compatibility
            func._security_obj = security

        @functools.wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            # TODO: Add security validation here
            # TODO: Add performance logging if enabled
            return await func(self, *args, **kwargs)

        return async_wrapper

    return decorator


def set_context(**context_data):
    """Set the current request context."""
    if not context_data:
        # Clear context when called with no arguments
        request_context.set(Context())
    else:
        # Create new context with updates
        current = request_context.get()
        # Update context fields
        new_context = current.model_copy()
        for key, value in context_data.items():
            # Skip fields that aren't meant to be set directly (like timestamp which is a datetime)
            if key == "timestamp" and not isinstance(value, datetime):
                # Store non-datetime timestamp values in metadata
                new_context.metadata[key] = value
            elif hasattr(new_context, key) and key not in ["request_id", "timestamp"]:
                # Set proper Context fields (but not auto-generated ones)
                setattr(new_context, key, value)
            else:
                # Store in metadata for unknown fields or special cases
                new_context.metadata[key] = value
        request_context.set(new_context)


def clear_context():
    """Clear the current request context."""
    request_context.set(Context())


def get_context() -> Context:
    """Get the current request context."""
    return request_context.get()


# @share is just @expose with security="peer"
def share(func: Callable) -> Callable:
    """Share a service method with peers (equivalent to @expose(security="peer"))."""
    return expose(security="peer")(func)


@asynccontextmanager
async def context_scope(**context_data):
    """Async context manager for setting request context with automatic cleanup."""
    # Get current context and create new one with updates
    current = request_context.get()
    new_context = current.model_copy()

    # Update context fields
    for key, value in context_data.items():
        # Skip fields that aren't meant to be set directly (like timestamp which is a datetime)
        if key == "timestamp" and not isinstance(value, datetime):
            # Store non-datetime timestamp values in metadata
            new_context.metadata[key] = value
        elif hasattr(new_context, key) and key not in ["request_id", "timestamp"]:
            # Set proper Context fields (but not auto-generated ones)
            setattr(new_context, key, value)
        else:
            # Store in metadata for unknown fields or special cases
            new_context.metadata[key] = value

    # Set the new context
    token = request_context.set(new_context)
    try:
        yield new_context
    finally:
        # Reset to previous context
        request_context.reset(token)
