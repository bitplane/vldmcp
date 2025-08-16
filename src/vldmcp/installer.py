"""Installer service for vldmcp."""

from pathlib import Path
from .service import Service
from . import paths
from . import crypto


class InstallerService(Service):
    """Service that handles vldmcp installation."""

    @classmethod
    def name(cls) -> str:
        return "installer"

    def start(self):
        """Not a running service - installation happens via install() method."""
        self._running = False

    def stop(self):
        """Not a running service."""
        self._running = False

    def install(self) -> bool:
        """Install and set up the vldmcp environment.

        Returns:
            True if installation succeeded, False otherwise
        """
        # Create all XDG directories with proper permissions
        paths.create_directories()

        # Ensure user identity key exists
        crypto.ensure_user_key()

        # Ensure secure permissions
        paths.ensure_secure_permissions()

        return True

    def uninstall(self, config: bool = False, purge: bool = False) -> list[tuple[str, Path]]:
        """Remove vldmcp installation.

        Args:
            config: Also remove configuration files
            purge: Remove everything including user keys

        Returns:
            List of (description, path) tuples for removed directories
        """
        import shutil

        dirs_removed = []

        # Always remove install and cache
        install_dir = paths.install_dir()
        if install_dir.exists():
            shutil.rmtree(install_dir)
            dirs_removed.append(("install data", install_dir))

        cache_dir = paths.cache_dir()
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            dirs_removed.append(("cache", cache_dir))

        # Config flag: also remove config and state
        if config or purge:
            config_dir = paths.config_dir()
            if config_dir.exists():
                shutil.rmtree(config_dir)
                dirs_removed.append(("configuration", config_dir))

            state_dir = paths.state_dir()
            if state_dir.exists():
                shutil.rmtree(state_dir)
                dirs_removed.append(("state data", state_dir))

            runtime_dir = paths.runtime_dir()
            if runtime_dir.exists():
                shutil.rmtree(runtime_dir)
                dirs_removed.append(("runtime data", runtime_dir))

        # Purge flag: also remove user data (including keys)
        if purge:
            data_dir = paths.data_dir()
            if data_dir.exists():
                shutil.rmtree(data_dir)
                dirs_removed.append(("user data", data_dir))

        return dirs_removed
