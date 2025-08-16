"""Shared pytest fixtures for vldmcp tests."""

import pytest
from vldmcp.file_service import FileService


@pytest.fixture
def xdg_dirs(tmp_path, monkeypatch):
    """Set up temporary XDG directories for testing.

    This fixture patches all XDG environment variables to use temporary directories,
    avoiding the need to repeat this setup in every test that uses paths.
    """
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    return tmp_path


@pytest.fixture
def file_service(xdg_dirs):
    """Get a FileService instance with temporary directories."""
    service = FileService()
    service.start()
    return service
