"""Service base class for the capability-based architecture."""

from abc import ABC


class Service(ABC):
    """Base class for services. Services can also host other services (recursive composition)."""

    version = "0.0.1"

    def __init__(self):
        self.host = None  # Parent service that hosts this one
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
        name = service.name()
        if name in self.services:
            raise ValueError(f"Service '{name}' already registered")
        self.services[name] = service
        service.host = self

    def remove_service(self, name: str):
        """Remove a child service from this service."""
        if name in self.services:
            service = self.services.pop(name)
            service.host = None

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
        if self.host:
            return self.host.call_service(target_service, method, request)

        raise RuntimeError(f"Service '{target_service}' not found")
