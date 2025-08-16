"""Machine sync tracking model."""

from typing import Optional
from datetime import datetime, UTC

from sqlmodel import SQLModel, Field


class Machine(SQLModel, table=True):
    """Track sync status with other machines/peers.

    Used to know what claims need to be pushed/pulled during sync.
    """

    # Machine identifier (could be Veilid DHT key, hostname, etc.)
    id: str = Field(primary_key=True, description="Unique identifier for the machine/peer")

    # Sync tracking
    last_sync_at: Optional[datetime] = Field(default=None, description="When we last synced with this machine")
    last_push_at: Optional[datetime] = Field(default=None, description="When we last pushed claims to this machine")
    last_pull_at: Optional[datetime] = Field(default=None, description="When we last pulled claims from this machine")

    # Machine metadata
    machine_type: str = Field(default="unknown", description="Type of machine (host, container, peer)")
    endpoint: Optional[str] = Field(default=None, description="How to connect to this machine")

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When we first saw this machine"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="When this record was last updated"
    )
