"""Identity service for managing claims and machine sync."""

from typing import Any, Optional
from datetime import datetime, UTC

from .crud import CRUDService
from .system.storage import Storage
from ..models.claim import Claim
from ..models.machine import Machine


class IDService(CRUDService):
    """Service for managing identity claims and machine synchronization."""

    def __init__(self, storage: Storage, parent=None):
        # Initialize CRUD service with Claim and Machine models
        super().__init__(storage, models=[Claim, Machine], parent=parent, name="id")

    def create_claim(self, payload_type: str, payload: dict[str, Any], signature: str, signer_pubkey: str) -> Claim:
        """Create a new generic claim.

        Args:
            payload_type: Type of claim (identity_claim, service_endorsement, etc.)
            payload: The claim data
            signature: Ed25519 signature of the payload
            signer_pubkey: Public key of the signer

        Returns:
            The created Claim
        """
        return self.upsert(
            "claim",
            unique_fields=["payload_type", "payload", "signer_pubkey"],
            payload_type=payload_type,
            payload=payload,
            signature=signature,
            signer_pubkey=signer_pubkey,
        )

    def create_identity_claim(
        self, identity_id: int, provider: str, value: str, claimed_by: int, signature: str, signer_pubkey: str
    ) -> Claim:
        """Create an identity claim (convenience method).

        Args:
            identity_id: The identity ID being claimed
            provider: Provider type (email, github, veilid, etc.)
            value: The identity value (email, username, key, etc.)
            claimed_by: ID of the person making the claim
            signature: Ed25519 signature
            signer_pubkey: Public key of signer

        Returns:
            The created Claim
        """
        payload = {"identity_id": identity_id, "provider": provider, "value": value, "claimed_by": claimed_by}

        return self.create_claim("identity_claim", payload, signature, signer_pubkey)

    def get_identity_claims(self, identity_id: int) -> list[Claim]:
        """Get all identity claims for a specific identity ID."""
        claims = self.read("claim", payload_type="identity_claim")
        return [c for c in claims if c.payload.get("identity_id") == identity_id]

    def get_claims_by_signer(self, signer_pubkey: str) -> list[Claim]:
        """Get all claims made by a specific signer."""
        return self.read("claim", signer_pubkey=signer_pubkey)

    def get_claims_for_provider_value(self, provider: str, value: str) -> list[Claim]:
        """Get all identity claims for a specific provider/value combination.

        This shows conflicts when multiple people claim the same identity.
        """
        claims = self.read("claim", payload_type="identity_claim")
        return [c for c in claims if c.payload.get("provider") == provider and c.payload.get("value") == value]

    def verify_claim(self, claim_id: int, verification_method: str = "manual") -> bool:
        """Mark a claim as verified.

        Args:
            claim_id: ID of the claim to verify
            verification_method: How verification was performed

        Returns:
            True if claim was found and updated
        """
        count = self.update(
            "claim", filters={"id": claim_id}, updates={"verified": True, "verified_at": datetime.now(UTC)}
        )
        return count > 0

    def get_verified_claims(self, identity_id: int) -> list[Claim]:
        """Get only verified identity claims for an identity."""
        claims = self.get_identity_claims(identity_id)
        return [c for c in claims if c.verified]

    def has_conflicts(self, provider: str, value: str) -> bool:
        """Check if multiple people claim the same provider/value."""
        claims = self.get_claims_for_provider_value(provider, value)
        unique_claimers = set(c.payload.get("claimed_by") for c in claims if c.payload.get("claimed_by"))
        return len(unique_claimers) > 1

    def get_identity_summary(self, identity_id: int) -> dict:
        """Get a summary of all claims for an identity."""
        claims = self.get_identity_claims(identity_id)

        summary = {
            "identity_id": identity_id,
            "total_claims": len(claims),
            "verified_claims": len([c for c in claims if c.verified]),
            "providers": list(set(c.payload.get("provider") for c in claims if c.payload.get("provider"))),
            "conflicts": {},
            "claims_by_provider": {},
        }

        # Group by provider
        for claim in claims:
            provider = claim.payload.get("provider")
            if not provider:
                continue

            if provider not in summary["claims_by_provider"]:
                summary["claims_by_provider"][provider] = []

            summary["claims_by_provider"][provider].append(
                {
                    "value": claim.payload.get("value"),
                    "verified": claim.verified,
                    "created_at": claim.created_at,
                    "signer": claim.signer_pubkey,
                }
            )

            # Check for conflicts
            conflicts = self.get_claims_for_provider_value(provider, claim.payload.get("value"))
            if len(conflicts) > 1:
                conflict_key = f"{provider}:{claim.payload.get('value')}"
                summary["conflicts"][conflict_key] = [
                    c.payload.get("claimed_by") for c in conflicts if c.payload.get("claimed_by")
                ]

        return summary

    # Machine sync methods

    def register_machine(
        self, machine_id: str, machine_type: str = "unknown", endpoint: Optional[str] = None
    ) -> Machine:
        """Register or update a machine for sync tracking."""
        return self.upsert("machine", unique_fields=["id"], id=machine_id, machine_type=machine_type, endpoint=endpoint)

    def update_sync_time(self, machine_id: str, sync_type: str = "sync") -> bool:
        """Update the last sync time for a machine.

        Args:
            machine_id: Machine identifier
            sync_type: Type of sync (sync, push, pull)
        """
        now = datetime.now(UTC)
        updates = {}

        if sync_type == "sync":
            updates["last_sync_at"] = now
        elif sync_type == "push":
            updates["last_push_at"] = now
        elif sync_type == "pull":
            updates["last_pull_at"] = now

        count = self.update("machine", {"id": machine_id}, updates)
        return count > 0

    def get_claims_since(self, since: datetime) -> list[Claim]:
        """Get claims updated since a timestamp (for incremental sync)."""
        return self.get_records_since("claim", since)

    def push_claims_to_machine(self, machine_id: str, since: Optional[datetime] = None) -> list[Claim]:
        """Get claims that should be pushed to a machine.

        Args:
            machine_id: Target machine ID
            since: Only get claims since this time (if None, get all)

        Returns:
            List of claims to push
        """
        if since:
            claims = self.get_claims_since(since)
        else:
            claims = self.read("claim")

        # Update push timestamp
        self.update_sync_time(machine_id, "push")

        return claims

    def receive_claims_from_machine(self, machine_id: str, claims: list[dict]) -> int:
        """Receive and merge claims from another machine.

        Args:
            machine_id: Source machine ID
            claims: List of claim data dicts

        Returns:
            Number of claims processed
        """
        processed = 0

        for claim_data in claims:
            try:
                # Upsert each claim
                self.upsert("claim", unique_fields=["payload_type", "payload", "signer_pubkey"], **claim_data)
                processed += 1
            except Exception:
                # Skip invalid claims
                continue

        # Update pull timestamp
        self.update_sync_time(machine_id, "pull")

        return processed
