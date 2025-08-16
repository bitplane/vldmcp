"""Security models for service method access control."""

from typing import List, Literal
from pydantic import BaseModel, Field


class SecurityRule(BaseModel):
    """A single security rule for method access control."""

    kind: Literal["user", "group", "path", "role"] = Field(description="Type of security rule")
    value: str = Field(description="Value to match (user ID, group name, role name, path pattern)")
    action: Literal["allow", "deny"] = Field(description="Action to take when rule matches")


class Security(BaseModel):
    """Security configuration for a service method."""

    rules: List[SecurityRule] = Field(description="List of security rules to evaluate")

    @classmethod
    def from_string(cls, security: str) -> "Security":
        """Convert simple string security to Security rules.

        Args:
            security: Simple security string like "owner" or "peer"

        Returns:
            Security object with appropriate rules
        """
        if security == "owner":
            return cls(rules=[SecurityRule(kind="role", value="owner", action="allow")])
        elif security == "peer":
            return cls(rules=[SecurityRule(kind="role", value="peer", action="allow")])
        else:
            # Treat as role by default
            return cls(rules=[SecurityRule(kind="role", value=security, action="allow")])

    def evaluate(self, context: dict) -> bool:
        """Evaluate security rules against a context.

        Args:
            context: Request context containing user info, roles, etc.

        Returns:
            True if access is allowed, False otherwise
        """
        # Default deny if no rules
        if not self.rules:
            return False

        # Process rules in order - first match wins
        for rule in self.rules:
            if self._rule_matches(rule, context):
                return rule.action == "allow"

        # No rules matched - default deny
        return False

    def _rule_matches(self, rule: SecurityRule, context: dict) -> bool:
        """Check if a rule matches the given context."""
        if rule.kind == "user":
            return context.get("user_id") == rule.value
        elif rule.kind == "role":
            return rule.value in context.get("roles", [])
        elif rule.kind == "group":
            return rule.value in context.get("groups", [])
        elif rule.kind == "path":
            # Simple path matching for now - could be enhanced with patterns
            return context.get("path", "").startswith(rule.value)

        return False
