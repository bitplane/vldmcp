"""Security service for validating method access and signing operations."""

from typing import Dict, Any, Optional
from ..service.base import Service
from ..models.call.security import Security
from ..models.call.context import Context


class SecurityService(Service):
    """Service for validating security rules and signing method calls."""

    def __init__(self, parent=None):
        super().__init__(parent=parent, name="security")

        # Default security configurations for built-in roles
        self.default_securities = {
            "owner": Security.from_string("owner"),
            "peer": Security.from_string("peer"),
        }

    async def validate_call(self, security: Security, context: Context) -> bool:
        """Validate that a context is allowed to make a call with given security.

        Args:
            security: Security configuration for the method
            context: Request context to validate

        Returns:
            True if call is allowed, False otherwise
        """
        return security.evaluate(context.model_dump())

    async def sign_call(self, context: Context, method_path: str) -> Dict[str, Any]:
        """Sign a method call for transport.

        Args:
            context: Request context
            method_path: Full path to the method being called

        Returns:
            Signed call data for transport
        """
        # TODO: Implement cryptographic signing
        # For now, return basic call metadata
        return {
            "context": context.to_jwt_payload(),
            "method_path": method_path,
            "timestamp": context.timestamp.isoformat(),
            "signature": f"signed_{context.request_id}",  # Placeholder
        }

    async def verify_call(self, signed_call: Dict[str, Any]) -> Optional[Context]:
        """Verify a signed method call from transport.

        Args:
            signed_call: Signed call data from transport

        Returns:
            Verified context if valid, None if invalid
        """
        # TODO: Implement signature verification
        # For now, just extract context
        context_data = signed_call.get("context", {})
        try:
            return Context.from_jwt_payload(context_data)
        except Exception:
            return None

    def get_security(self, security_spec: str) -> Security:
        """Get Security object from string specification.

        Args:
            security_spec: Security specification ("owner", "peer", or custom)

        Returns:
            Security object
        """
        if security_spec in self.default_securities:
            return self.default_securities[security_spec]

        return Security.from_string(security_spec)
