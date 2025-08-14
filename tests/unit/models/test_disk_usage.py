"""Tests for the disk_usage model."""

from vldmcp.models.disk_usage import DiskUsage, InstallUsage, McpUsage


def test_disk_usage_total_calculates_correctly():
    """Test that the total property calculates the sum of all usage fields."""
    usage = DiskUsage(
        config=10,
        install=InstallUsage(image=20, data=30),
        mcp=McpUsage(repos=40, images=50, data=60),
        www=70,
    )
    assert usage.total == 280


def test_disk_usage_total_handles_human_readable_strings():
    """Test that the total property returns 'N/A' when fields are strings."""
    usage = DiskUsage(
        config="10B",
        install=InstallUsage(image="20B", data="30B"),
        mcp=McpUsage(repos="40B", images="50B", data="60B"),
        www="70B",
    )
    assert usage.total == "N/A"
