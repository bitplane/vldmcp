"""Generic claim model for cryptographically signed statements."""

from typing import Any, Optional
from datetime import datetime, UTC

from sqlmodel import SQLModel, Field, JSON, Column
from pydantic import ConfigDict


class Claim(SQLModel, table=True):
    """A generic cryptographically signed claim.

    Can represent any type of signed statement - identity claims,
    service endorsements, capability grants, etc.
    """

    # Primary key - auto-incrementing ID
    id: Optional[int] = Field(default=None, primary_key=True)

    # Claim content and type
    payload_type: str = Field(description="Type of claim (identity_claim, service_endorsement, etc.)")
    payload: dict[str, Any] = Field(sa_column=Column(JSON), description="The claim data")

    # Cryptographic proof
    signature: str = Field(description="Ed25519 signature of the payload")
    signer_pubkey: str = Field(description="Public key of the signer")

    # Automatic timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When claim was created")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="When claim was last updated")

    # Verification status
    verified: bool = Field(default=False, description="Whether signature has been verified")
    verified_at: Optional[datetime] = Field(default=None, description="When verification occurred")

    model_config = ConfigDict(table_args={"sqlite_unique": [["payload_type", "payload", "signer_pubkey"]]})
