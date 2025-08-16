"""Root service that manages the entire service tree."""

from .base import Service


# Root is just a Service with an API child
def create_root():
    """Create the root service with API hierarchy."""
    root = Service(name="root")
    Service(name="api", parent=root)
    return root
