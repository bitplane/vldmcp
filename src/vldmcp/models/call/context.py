"""Context model for service method calls."""

from typing import List, Optional, Dict, Any
from datetime import datetime, UTC
from uuid import uuid4
from pydantic import BaseModel, Field


class Context(BaseModel):
    """Request context for service method calls.

    This model supports serialization to JWT tokens and capnproto
    for transport across different communication layers.
    """

    # Request identification
    request_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique request identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Request timestamp")

    # User identity and authorization
    user_id: Optional[str] = Field(None, description="User identifier")
    roles: List[str] = Field(default_factory=list, description="User roles (owner, peer, admin, etc.)")
    groups: List[str] = Field(default_factory=list, description="User groups")
    permissions: List[str] = Field(default_factory=list, description="Specific permissions")

    # Service and method context
    service_path: Optional[str] = Field(None, description="Full path to the service being called")
    method_name: Optional[str] = Field(None, description="Name of the method being called")

    # Transport context
    transport: Optional[str] = Field(None, description="Transport layer (http, veilid, direct)")
    source_node: Optional[str] = Field(None, description="Source node ID for P2P calls")

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context data")

    def has_role(self, role: str) -> bool:
        """Check if context has a specific role."""
        return role in self.roles

    def has_permission(self, permission: str) -> bool:
        """Check if context has a specific permission."""
        return permission in self.permissions

    def has_group(self, group: str) -> bool:
        """Check if context belongs to a specific group."""
        return group in self.groups

    def to_jwt_payload(self) -> Dict[str, Any]:
        """Convert context to JWT payload format."""
        return {
            "sub": self.user_id,  # Subject (user)
            "iat": int(self.timestamp.timestamp()),  # Issued at
            "jti": self.request_id,  # JWT ID
            "roles": self.roles,
            "groups": self.groups,
            "permissions": self.permissions,
            "service_path": self.service_path,
            "method_name": self.method_name,
            "transport": self.transport,
            "source_node": self.source_node,
            "metadata": self.metadata,
        }

    @classmethod
    def from_jwt_payload(cls, payload: Dict[str, Any]) -> "Context":
        """Create context from JWT payload."""
        return cls(
            user_id=payload.get("sub"),
            request_id=payload.get("jti", str(uuid4())),
            timestamp=datetime.fromtimestamp(payload.get("iat", datetime.now(UTC).timestamp()), UTC),
            roles=payload.get("roles", []),
            groups=payload.get("groups", []),
            permissions=payload.get("permissions", []),
            service_path=payload.get("service_path"),
            method_name=payload.get("method_name"),
            transport=payload.get("transport"),
            source_node=payload.get("source_node"),
            metadata=payload.get("metadata", {}),
        )
