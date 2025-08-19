"""Tests for ClaimService."""

import pytest
from datetime import datetime, UTC, timedelta
from tempfile import TemporaryDirectory
from pathlib import Path

from vldmcp.service.claim import ClaimService
from vldmcp.service.system.storage import Storage


@pytest.fixture
def temp_storage():
    """Create temporary storage for testing."""
    with TemporaryDirectory() as temp_dir:
        storage = Storage()
        storage._data_home = Path(temp_dir)
        yield storage


@pytest.fixture
def id_service(temp_storage):
    """Create a ClaimService with temporary storage."""
    service = ClaimService(temp_storage)
    # Clear any existing data for clean tests
    service.delete("claim")
    service.delete("machine")
    yield service
    # Clean up engine connections
    service.stop()


def test_create_claim(id_service):
    """Test creating a new claim."""
    claim = id_service.create_claim(
        payload_type="test_claim",
        payload={"test_data": "value"},
        signature="test_signature",
        signer_pubkey="test_pubkey",
    )

    assert claim.payload_type == "test_claim"
    assert claim.payload == {"test_data": "value"}
    assert claim.signature == "test_signature"
    assert claim.signer_pubkey == "test_pubkey"
    assert not claim.verified
    assert claim.verified_at is None


def test_create_identity_claim(id_service):
    """Test creating an identity claim."""
    claim = id_service.create_identity_claim(
        identity_id=123,
        provider="github",
        value="testuser",
        claimed_by=456,
        signature="test_sig",
        signer_pubkey="test_key",
    )

    assert claim.payload_type == "identity_claim"
    assert claim.payload["identity_id"] == 123
    assert claim.payload["provider"] == "github"
    assert claim.payload["value"] == "testuser"
    assert claim.payload["claimed_by"] == 456


def test_get_identity_claims(id_service):
    """Test getting claims for specific identity."""
    # Create claims for different identities
    id_service.create_identity_claim(123, "github", "user1", 456, "sig1", "key1")
    id_service.create_identity_claim(123, "email", "user1@test.com", 456, "sig2", "key1")
    id_service.create_identity_claim(789, "github", "user2", 999, "sig3", "key2")

    claims_123 = id_service.get_identity_claims(123)
    claims_789 = id_service.get_identity_claims(789)

    assert len(claims_123) == 2
    assert len(claims_789) == 1

    providers_123 = [c.payload["provider"] for c in claims_123]
    assert "github" in providers_123
    assert "email" in providers_123


def test_get_claims_by_signer(id_service):
    """Test getting claims by signer."""
    id_service.create_identity_claim(123, "github", "user1", 456, "sig1", "key1")
    id_service.create_identity_claim(789, "email", "user2@test.com", 456, "sig2", "key1")
    id_service.create_identity_claim(999, "github", "user3", 777, "sig3", "key2")

    claims_key1 = id_service.get_claims_by_signer("key1")
    claims_key2 = id_service.get_claims_by_signer("key2")

    assert len(claims_key1) == 2
    assert len(claims_key2) == 1


def test_get_claims_for_provider_value(id_service):
    """Test getting claims for specific provider/value."""
    # Multiple people claiming same GitHub username
    id_service.create_identity_claim(123, "github", "popular_username", 456, "sig1", "key1")
    id_service.create_identity_claim(789, "github", "popular_username", 999, "sig2", "key2")
    id_service.create_identity_claim(123, "github", "unique_username", 456, "sig3", "key1")

    popular_claims = id_service.get_claims_for_provider_value("github", "popular_username")
    unique_claims = id_service.get_claims_for_provider_value("github", "unique_username")

    assert len(popular_claims) == 2
    assert len(unique_claims) == 1


def test_verify_claim(id_service):
    """Test verifying a claim."""
    claim = id_service.create_identity_claim(123, "github", "user1", 456, "sig1", "key1")

    # Initially not verified
    assert not claim.verified
    assert claim.verified_at is None

    # Verify the claim
    result = id_service.verify_claim(claim.id)
    assert result is True

    # Check verification status
    updated_claims = id_service.read("claim", id=claim.id)
    assert len(updated_claims) == 1
    updated_claim = updated_claims[0]
    assert updated_claim.verified is True
    assert updated_claim.verified_at is not None


def test_verify_nonexistent_claim(id_service):
    """Test verifying a claim that doesn't exist."""
    result = id_service.verify_claim(99999)
    assert result is False


def test_get_verified_claims(id_service):
    """Test getting only verified claims."""
    claim1 = id_service.create_identity_claim(123, "github", "user1", 456, "sig1", "key1")
    id_service.create_identity_claim(123, "email", "user1@test.com", 456, "sig2", "key1")

    # Verify only one claim
    id_service.verify_claim(claim1.id)

    verified_claims = id_service.get_verified_claims(123)
    assert len(verified_claims) == 1
    assert verified_claims[0].id == claim1.id


def test_has_conflicts(id_service):
    """Test detecting conflicts for provider/value."""
    # No conflict initially
    assert not id_service.has_conflicts("github", "username")

    # Single claim - no conflict
    id_service.create_identity_claim(123, "github", "username", 456, "sig1", "key1")
    assert not id_service.has_conflicts("github", "username")

    # Multiple people claiming same identity - conflict
    id_service.create_identity_claim(789, "github", "username", 999, "sig2", "key2")
    assert id_service.has_conflicts("github", "username")


def test_get_identity_summary(id_service):
    """Test getting identity summary."""
    # Create various claims for identity 123
    id_service.create_identity_claim(123, "github", "user123", 456, "sig1", "key1")
    claim2 = id_service.create_identity_claim(123, "email", "user123@test.com", 456, "sig2", "key1")
    id_service.create_identity_claim(123, "veilid", "VLD0:abc123", 456, "sig3", "key1")

    # Create a conflict
    id_service.create_identity_claim(789, "github", "user123", 999, "sig4", "key2")

    # Verify one claim
    id_service.verify_claim(claim2.id)

    summary = id_service.get_identity_summary(123)

    assert summary["identity_id"] == 123
    assert summary["total_claims"] == 3
    assert summary["verified_claims"] == 1
    assert set(summary["providers"]) == {"github", "email", "veilid"}
    assert len(summary["claims_by_provider"]) == 3
    assert "github:user123" in summary["conflicts"]


def test_register_machine(id_service):
    """Test registering a machine."""
    machine = id_service.register_machine("machine1", "container", "tcp://192.168.1.100:8080")

    assert machine.id == "machine1"
    assert machine.machine_type == "container"
    assert machine.endpoint == "tcp://192.168.1.100:8080"


def test_register_machine_upsert(id_service):
    """Test that registering same machine updates it."""
    # First registration
    machine1 = id_service.register_machine("machine1", "host", "tcp://192.168.1.100:8080")

    # Second registration with different type
    machine2 = id_service.register_machine("machine1", "container", "tcp://192.168.1.100:8081")

    # Should be same record, updated
    assert machine1.id == machine2.id
    assert machine2.machine_type == "container"
    assert machine2.endpoint == "tcp://192.168.1.100:8081"

    # Should only be one machine record
    machines = id_service.read("machine")
    assert len(machines) == 1


def test_update_sync_time(id_service):
    """Test updating sync timestamps."""
    id_service.register_machine("machine1")

    # Test different sync types
    assert id_service.update_sync_time("machine1", "sync") is True
    assert id_service.update_sync_time("machine1", "push") is True
    assert id_service.update_sync_time("machine1", "pull") is True

    # Test nonexistent machine
    assert id_service.update_sync_time("nonexistent", "sync") is False

    # Verify timestamps were set
    machines = id_service.read("machine", id="machine1")
    machine = machines[0]
    assert machine.last_sync_at is not None
    assert machine.last_push_at is not None
    assert machine.last_pull_at is not None


def test_get_claims_since(id_service):
    """Test getting claims since timestamp."""
    past_time = datetime.now(UTC) - timedelta(hours=1)

    # Create a claim
    claim = id_service.create_identity_claim(123, "github", "user1", 456, "sig1", "key1")

    # Should find claim
    recent_claims = id_service.get_claims_since(past_time)
    assert len(recent_claims) >= 1
    assert claim.id in [c.id for c in recent_claims]

    # Should not find from future
    future_time = datetime.now(UTC) + timedelta(hours=1)
    future_claims = id_service.get_claims_since(future_time)
    assert len(future_claims) == 0


def test_push_claims_to_machine(id_service):
    """Test pushing claims to machine."""
    id_service.register_machine("machine1")
    id_service.create_identity_claim(123, "github", "user1", 456, "sig1", "key1")
    id_service.create_identity_claim(456, "email", "user2@test.com", 789, "sig2", "key2")

    # Push all claims
    claims = id_service.push_claims_to_machine("machine1")
    assert len(claims) == 2

    # Push since timestamp (should find both)
    past_time = datetime.now(UTC) - timedelta(hours=1)
    recent_claims = id_service.push_claims_to_machine("machine1", since=past_time)
    assert len(recent_claims) == 2

    # Verify push timestamp was updated
    machines = id_service.read("machine", id="machine1")
    assert machines[0].last_push_at is not None


def test_receive_claims_from_machine(id_service):
    """Test receiving claims from machine."""
    id_service.register_machine("machine2")

    claims_data = [
        {
            "payload_type": "identity_claim",
            "payload": {"identity_id": 123, "provider": "github", "value": "user1", "claimed_by": 456},
            "signature": "sig1",
            "signer_pubkey": "key1",
        },
        {
            "payload_type": "identity_claim",
            "payload": {"identity_id": 789, "provider": "email", "value": "user2@test.com", "claimed_by": 999},
            "signature": "sig2",
            "signer_pubkey": "key2",
        },
        {
            # Invalid claim data - should be skipped
            "payload_type": "invalid_claim"
            # Missing required fields
        },
    ]

    processed = id_service.receive_claims_from_machine("machine2", claims_data)
    assert processed == 2  # Only 2 valid claims processed

    # Verify claims were created
    all_claims = id_service.read("claim")
    assert len(all_claims) == 2

    # Verify pull timestamp was updated
    machines = id_service.read("machine", id="machine2")
    assert machines[0].last_pull_at is not None


def test_claim_upsert_behavior(id_service):
    """Test that claims are upserted correctly based on unique fields."""
    # Create initial claim
    claim1 = id_service.create_claim(
        payload_type="test_type", payload={"test": "data"}, signature="sig1", signer_pubkey="key1"
    )

    # Create identical claim - should be same record
    claim2 = id_service.create_claim(
        payload_type="test_type", payload={"test": "data"}, signature="sig1", signer_pubkey="key1"
    )

    assert claim1.id == claim2.id

    # Create claim with different signer - should be new record
    claim3 = id_service.create_claim(
        payload_type="test_type",
        payload={"test": "data"},
        signature="sig2",
        signer_pubkey="key2",  # Different signer
    )

    assert claim1.id != claim3.id

    # Should have 2 claims total
    all_claims = id_service.read("claim")
    assert len(all_claims) == 2
