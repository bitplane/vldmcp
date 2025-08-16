"""Service base class for the capability-based architecture."""

import asyncio


class Service:
    """Base class for services. Services can also host other services (recursive composition)."""

    version = "0.0.1"

    def __init__(self, parent=None):
        self.parent = parent
        self._running = False
        self.children = {}  # Child services this service hosts

        # Auto-register with parent if provided
        if parent:
            parent.children[self.name()] = self

    @classmethod
    def name(cls) -> str:
        """Get the service name (derived from class name)."""
        name = cls.__name__
        # Remove parent class name suffix if present
        parent_name = cls.__bases__[0].__name__
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
