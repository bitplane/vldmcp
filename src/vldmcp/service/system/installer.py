"""Installer service for vldmcp."""

from pathlib import Path
from .service import Service
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
        self.parent.files.create_directories()

        # Ensure user identity key exists
        crypto.ensure_user_key(self.parent.files)

        # Ensure secure permissions
        self.parent.files.ensure_secure_permissions()

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
        install_dir = self.parent.files.install_dir()
        if install_dir.exists():
            shutil.rmtree(install_dir)
            dirs_removed.append(("install data", install_dir))

        cache_dir = self.parent.files.cache_dir()
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            dirs_removed.append(("cache", cache_dir))

        # Config flag: also remove config and state
        if config or purge:
            config_dir = self.parent.files.config_dir()
            if config_dir.exists():
                shutil.rmtree(config_dir)
                dirs_removed.append(("configuration", config_dir))

            state_dir = self.parent.files.state_dir()
            if state_dir.exists():
                shutil.rmtree(state_dir)
                dirs_removed.append(("state data", state_dir))

            runtime_dir = self.parent.files.runtime_dir()
            if runtime_dir.exists():
                shutil.rmtree(runtime_dir)
                dirs_removed.append(("runtime data", runtime_dir))

        # Purge flag: also remove user data (including keys)
        if purge:
            data_dir = self.parent.files.data_dir()
            if data_dir.exists():
                shutil.rmtree(data_dir)
                dirs_removed.append(("user data", data_dir))

        return dirs_removed
