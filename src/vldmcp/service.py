"""Service base class for the capability-based architecture."""

from abc import ABC


class Service(ABC):
    """Base class for services. Services can also host other services (recursive composition)."""

    version = "0.0.1"

    def __init__(self):
        self.parent = None  # Immediate parent service
        self.root = None  # Top-level service in the hierarchy
        self._running = False
        self.services = {}  # Child services this service hosts

    @classmethod
    def name(cls) -> str:
        """Get the service name (defaults to class name)."""
        return cls.__name__

    # Service lifecycle
    def start(self):
        """Start this service and all its children."""
        self._running = True
        # Start all child services
        for service in self.services.values():
            service.start()

    def stop(self):
        """Stop this service and all its children."""
        # Stop all child services first
        for service in self.services.values():
            service.stop()
        self._running = False

    async def run(self):
        """Main run loop for this service. Override for custom behavior."""
        # Default: just keep running while status is running
        import asyncio

        while self._running:
            await asyncio.sleep(1.0)

    def status(self) -> str:
        """Get the status of this service."""
        if self._running:
            return "running"
        return "stopped"

    # Hosting capabilities - services can host other services
    def add_service(self, service):
        """Add a child service to this service."""
        # Validate that it's actually a service
        if not isinstance(service, Service):
            raise TypeError(f"Expected Service instance, got {type(service)}")

        name = service.name()

        # Check if name already exists in services
        if name in self.services:
            raise ValueError(f"Service '{name}' already registered")

        # Check if attribute already exists and isn't a service
        if hasattr(self, name) and not isinstance(getattr(self, name), Service):
            existing = getattr(self, name)
            raise ValueError(f"{self.name()} already has {name} of type {type(existing)}")

        self.services[name] = service
        # Also add to __dict__ for attribute access
        setattr(self, name, service)
        service.parent = self
        service.root = self.root if self.root else self

    def remove_service(self, name: str):
        """Remove a child service from this service."""
        if name in self.services:
            service = self.services.pop(name)
            # Also remove from __dict__
            if hasattr(self, name):
                delattr(self, name)
            service.parent = None
            service.root = None

    def get_service(self, name: str):
        """Get a child service by name."""
        return self.services.get(name)

    def start_service(self, name: str):
        """Start a specific child service."""
        service = self.get_service(name)
        if service:
            service.start()

    def stop_service(self, name: str):
        """Stop a specific child service."""
        service = self.get_service(name)
        if service:
            service.stop()

    def get_all_statuses(self) -> dict[str, str]:
        """Get status of all child services."""
        statuses = {}
        for name, service in self.services.items():
            statuses[name] = service.status()
        return statuses

    def call_service(self, target_service: str, method: str, request: dict) -> dict:
        """Call another service (either child or ask host to route)."""
        # First try children
        service = self.get_service(target_service)
        if service:
            # TODO: Implement method dispatch
            raise NotImplementedError("Method dispatch not yet implemented")

        # Ask parent to route
        if self.parent:
            return self.parent.call_service(target_service, method, request)

        raise RuntimeError(f"Service '{target_service}' not found")
