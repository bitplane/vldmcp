"""Tests for info models."""

import pytest
from vldmcp.models.info import ClientInfo, ServerInfo, InfoResponse
from vldmcp import __version__


def test_client_info_defaults():
    """Test ClientInfo with default values."""
    info = ClientInfo(runtime_type="native", server_status="running")

    assert info.client_version == __version__
    assert info.runtime_type == "native"
    assert info.server_status == "running"
    assert info.server_pid is None
    assert info.ports == []


def test_client_info_full():
    """Test ClientInfo with all fields populated."""
    info = ClientInfo(
        client_version="1.0.0",
        runtime_type="podman",
        server_status="stopped",
        server_pid="12345",
        ports=["8080:8080", "9090:9090"],
    )

    assert info.client_version == "1.0.0"
    assert info.runtime_type == "podman"
    assert info.server_status == "stopped"
    assert info.server_pid == "12345"
    assert info.ports == ["8080:8080", "9090:9090"]


def test_server_info_defaults():
    """Test ServerInfo with default values."""
    info = ServerInfo()

    assert info.server_version is None
    assert info.server_pid is None
    assert info.veilid_status is None
    assert info.peer_count is None
    assert info.tool_count is None


def test_server_info_full():
    """Test ServerInfo with all fields populated."""
    info = ServerInfo(server_version="1.0.0", server_pid=12345, veilid_status="connected", peer_count=5, tool_count=10)

    assert info.server_version == "1.0.0"
    assert info.server_pid == 12345
    assert info.veilid_status == "connected"
    assert info.peer_count == 5
    assert info.tool_count == 10


def test_info_response():
    """Test InfoResponse combining client and server info."""
    client = ClientInfo(runtime_type="native", server_status="running")
    server = ServerInfo(server_version="1.0.0", peer_count=3)

    response = InfoResponse(client=client, server=server)

    assert response.client == client
    assert response.server == server
    assert response.client.runtime_type == "native"
    assert response.server.peer_count == 3


def test_client_info_serialization():
    """Test ClientInfo can be serialized to dict."""
    info = ClientInfo(runtime_type="podman", server_status="running", server_pid="999", ports=["8080:8080"])

    data = info.model_dump()

    assert data["runtime_type"] == "podman"
    assert data["server_status"] == "running"
    assert data["server_pid"] == "999"
    assert data["ports"] == ["8080:8080"]
    assert "client_version" in data


def test_server_info_serialization():
    """Test ServerInfo can be serialized to dict."""
    info = ServerInfo(server_version="1.0.0", tool_count=5)

    data = info.model_dump()

    assert data["server_version"] == "1.0.0"
    assert data["tool_count"] == 5
    assert data["server_pid"] is None  # Default None values included


def test_info_response_serialization():
    """Test InfoResponse can be serialized to dict."""
    client = ClientInfo(runtime_type="native", server_status="stopped")
    server = ServerInfo(peer_count=0)
    response = InfoResponse(client=client, server=server)

    data = response.model_dump()

    assert "client" in data
    assert "server" in data
    assert data["client"]["runtime_type"] == "native"
    assert data["server"]["peer_count"] == 0


def test_client_info_validation():
    """Test ClientInfo validates required fields."""
    with pytest.raises(ValueError):
        ClientInfo()  # Missing required runtime_type and server_status

    with pytest.raises(ValueError):
        ClientInfo(runtime_type="native")  # Missing server_status

    with pytest.raises(ValueError):
        ClientInfo(server_status="running")  # Missing runtime_type


def test_server_info_type_validation():
    """Test ServerInfo validates field types."""
    # Valid
    info = ServerInfo(server_pid=123, peer_count=5)
    assert info.server_pid == 123

    # Invalid types should be caught by Pydantic
    with pytest.raises(ValueError):
        ServerInfo(server_pid="not-a-number")  # String instead of int
