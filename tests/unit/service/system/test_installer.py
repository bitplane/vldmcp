"""Tests for installer service."""

import pytest
from unittest.mock import MagicMock, patch

from vldmcp.service.system.installer import InstallerService


def test_installer_service_name():
    """Test installer service name."""
    assert InstallerService.name() == "installer"


def test_installer_start_stop():
    """Test installer start/stop - should not be a running service."""
    installer = InstallerService()

    installer.start()
    assert installer._running is False

    installer.stop()
    assert installer._running is False


def test_uninstall_signature():
    """Test that uninstall method has expected signature."""
    installer = InstallerService()

    # Test that method exists and accepts flags
    assert hasattr(installer, "uninstall")
    assert callable(installer.uninstall)

    # Method should accept config and purge parameters
    import inspect

    sig = inspect.signature(installer.uninstall)
    assert "config" in sig.parameters
    assert "purge" in sig.parameters


def test_install_calls_storage_methods():
    """Test that install calls the required storage methods."""
    installer = InstallerService()

    # Create mock parent with storage
    mock_storage = MagicMock()
    mock_parent = MagicMock()
    mock_parent.storage = mock_storage
    installer.parent = mock_parent

    # Mock the crypto module
    with patch("vldmcp.service.system.installer.crypto.ensure_user_key") as mock_key:
        result = installer.install()

        assert result is True
        mock_storage.create_directories.assert_called_once()
        mock_storage.ensure_secure_permissions.assert_called_once()
        mock_key.assert_called_once_with(mock_storage)


def test_install_without_parent_fails():
    """Test that install fails gracefully without parent."""
    installer = InstallerService()
    # No parent set

    # Should not crash, but will likely raise AttributeError
    with pytest.raises(AttributeError):
        installer.install()
