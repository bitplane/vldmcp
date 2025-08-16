"""Service base class for the capability-based architecture."""

import asyncio


class Service:
    """Base class for services. Services can also host other services (recursive composition)."""

    version = "0.0.1"

    def __init__(self, parent=None, name=None):
        self.parent = parent
        self._running = False
        self.children = {}  # Child services this service hosts
        self.name = name or self._get_name()
        self.path = self.name  # Path in service tree (can be made empty for merging)

        # Auto-register with parent if provided
        if parent:
            parent.children[self.name] = self

    def _get_name(self) -> str:
        """Get the service name (derived from class name)."""
        name = self.__class__.__name__
        # Remove parent class name suffix if present
        parent_name = self.__class__.__bases__[0].__name__
        if name.endswith(parent_name) and name != parent_name:
            name = name[: -len(parent_name)]
        return name.lower()

    def __getattr__(self, name):
        """Forward attribute access to children if not found."""
        if name in self.children:
            return self.children[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    # Service lifecycle
    def start(self):
        """Start this service and all its children."""
        self._running = True
        # Start all child services
        for service in self.children.values():
            service.start()

    def stop(self):
        """Stop this service and all its children."""
        # Stop all child services first
        for service in self.children.values():
            service.stop()
        self._running = False

    async def run(self):
        """Run this service and all children concurrently."""
        if self.children:
            await asyncio.gather(*[child.run() for child in self.children.values()])
        else:
            # Default: just keep running while status is running
            while self._running:
                await asyncio.sleep(1.0)

    def status(self) -> str:
        """Get the status of this service."""
        if self._running:
            return "running"
        return "stopped"

    def remove(self, config: bool = False, purge: bool = False) -> list[tuple[str, str]]:
        """Remove this service and clean up resources.

        Default implementation does nothing.
        Subclasses should override to provide cleanup logic.

        Args:
            config: If True, also remove configuration files
            purge: If True, also remove all user data

        Returns:
            List of (description, path) tuples for removed items
        """
        return []

    def get_all_statuses(self) -> dict[str, str]:
        """Get status of all child services."""
        statuses = {}
        for name, service in self.children.items():
            statuses[name] = service.status()
        return statuses

    def full_path(self) -> str:
        """Get the full path of this service in the tree."""
        parts = []
        current = self
        while current:
            if current.path:  # Skip empty paths from merged services
                parts.append(current.path)
            current = current.parent
        return "/" + "/".join(reversed(parts)) if parts else "/"

    def __add__(self, other):
        """Merge two services into a MergedService."""
        if isinstance(other, MergedService):
            # If other is already merged, extend it
            other_services = [svc for key, svc in other.children.items() if key.startswith("_merged_")]
            services = [self] + other_services
        elif isinstance(self, MergedService):
            # If self is merged, extend it
            self_services = [svc for key, svc in self.children.items() if key.startswith("_merged_")]
            services = self_services + [other]
        else:
            # Both are regular services
            services = [self, other]

        return MergedService(services)


def dispatch_any(obj_list, method_name, *args, **kwargs):
    """Try calling method on each object until one succeeds.

    Args:
        obj_list: List of objects to try
        method_name: Name of method to call
        *args: Positional arguments to pass
        **kwargs: Keyword arguments to pass

    Returns:
        Result of first successful call

    Raises:
        AttributeError: If no object has the method
    """
    for obj in obj_list:
        if hasattr(obj, method_name):
            method = getattr(obj, method_name)
            if callable(method):
                return method(*args, **kwargs)

    raise AttributeError(f"No object in list has callable method '{method_name}'")


class MergedService(Service):
    """Service that merges multiple services together with invisible paths."""

    def __init__(self, services: list[Service], parent=None):
        # Use first service's name and path
        first = services[0] if services else None
        name = first.name if first else "merged"
        super().__init__(parent, name=name)

        # Merged service takes the path of the first service
        self.path = first.path if first else ""

        # Add all services as children with empty paths (invisible in routing)
        for service in services:
            service.parent = self
            service.path = "" if service != first else service.path
            # Use a unique key since they might have name conflicts
            self.children[f"_merged_{id(service)}"] = service

    def __getattr__(self, name):
        """Search for attribute in merged services (reverse order for priority)."""
        # First check if it's in our __dict__ to avoid infinite recursion
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        # Get services from children (they're stored with _merged_ prefix)
        services = [svc for key, svc in self.children.items() if key.startswith("_merged_")]

        # Search services in reverse order (later services override earlier)
        for service in reversed(services):
            try:
                return getattr(service, name)
            except AttributeError:
                continue

        # If not found in merged services, check regular children
        if name in self.children:
            return self.children[name]

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    # Lifecycle methods are inherited from Service and work with children automatically
