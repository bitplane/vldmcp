"""Configuration service for vldmcp."""

import os
import tomllib
import tomli_w
from pathlib import Path

from .. import Service
from ...models.config import Config, PlatformConfig, NativeConfig, PodmanConfig


class ConfigService(Service):
    """Service that manages vldmcp configuration."""

    def __init__(self):
        super().__init__()
        self._config: Config | None = None

    @property
    def _config_path(self) -> Path:
        """Get config file path from StorageService if available, otherwise use XDG."""
        if self.parent and hasattr(self.parent, "storage"):
            return self.parent.storage.config_dir() / "config.toml"
        # Fallback to XDG paths for standalone usage
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "vldmcp" / "config.toml"
        return Path.home() / ".config" / "vldmcp" / "config.toml"

    @classmethod
    def name(cls) -> str:
        return "config"

    def start(self):
        """Load configuration on start."""
        self.load()
        self._running = True

    def stop(self):
        """Save configuration on stop."""
        if self._config:
            self.save()
        self._running = False

    def load(self) -> Config:
        """Load configuration from disk.

        Returns:
            Loaded configuration object
        """
        if self._config is not None:
            return self._config

        if self._config_path.exists():
            try:
                with open(self._config_path, "rb") as f:
                    data = tomllib.load(f)
                self._config = Config.model_validate(data)
            except (tomllib.TOMLDecodeError, OSError, ValueError) as e:
                # If config is invalid, fall back to defaults and save
                print(f"Warning: Invalid config file {self._config_path}: {e}")
                print("Using default configuration")
                self._config = Config()
                self.save()
        else:
            # Create default config
            self._config = Config()
            self.save()

        return self._config

    def save(self) -> None:
        """Save current configuration to disk."""
        if self._config is None:
            return

        self._config_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict and save as TOML
        config_dict = self._config.model_dump(mode="json", exclude_defaults=False)
        with open(self._config_path, "wb") as f:
            tomli_w.dump(config_dict, f)

    def get(self) -> Config:
        """Get current configuration.

        Returns:
            Current configuration object
        """
        if not self._config:
            self.load()
        return self._config

    def set_platform_type(self, platform_type: str) -> None:
        """Set the platform type in configuration.

        Args:
            platform_type: Platform type to set (native, podman, etc)
        """
        config = self.get()

        # Create new platform config based on type
        if platform_type == "native":
            config.platform = NativeConfig()
        elif platform_type == "podman":
            config.platform = PodmanConfig()
        else:
            config.platform = PlatformConfig(type=platform_type)

        self.save()

    def update(self, **kwargs) -> None:
        """Update configuration values.

        Args:
            **kwargs: Configuration values to update
        """
        if not self._config:
            self.load()

        # Update config with new values
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

        self.save()


# Global config service instance for backward compatibility
_global_config_service = None


def get_config() -> Config:
    """Get the current configuration.

    This function provides backward compatibility with old config.py imports.
    """
    global _global_config_service
    if _global_config_service is None:
        _global_config_service = ConfigService()
        _global_config_service.start()
    return _global_config_service.get()


def set_platform_type(platform_type: str) -> None:
    """Set the platform type in configuration.

    This function provides backward compatibility with old config.py imports.
    """
    global _global_config_service
    if _global_config_service is None:
        _global_config_service = ConfigService()
        _global_config_service.start()
    _global_config_service.set_platform_type(platform_type)
